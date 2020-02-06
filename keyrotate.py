from github import Github
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import json
import jenkins
import os
from datetime import datetime
from xml.etree import ElementTree

server = jenkins.Jenkins('https://myjenkins.server.fqdn/jenkins', username='--------------------', password='------------------------------')
g = Github(base_url="https://mygithub_enterprise.server.fqdn/api/v3", login_or_token='------------------------------')


if not os.path.exists("./key_gen"):
    os.makedirs("./key_gen")

with open("./cred_mapping_table.json","r") as f:
    jsonf=f.read()
    mycred=json.loads(jsonf)


ds = datetime.now().strftime('%Y%m')

for item in mycred:
    repo_name=item["repo_name"]
    key_title=item["key_title"]
    jenkins_project_folder=item["jenkins_project_folder"]

    #gen key
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()).decode('utf-8')
    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    ).decode('utf-8')


    # Github part
    repo = g.get_repo(repo_name)
    #remove old key
    for key in repo.get_keys():
        if key_title in key.title:
            key.delete()
            break

    key_title_adc="{}-{}".format(key_title, ds)
    if 'read_only' in item.keys():
        read_only = item['read_only']
    else:
        read_only = True
    repo.create_key(title= key_title_adc,key=public_key,read_only=read_only)

    print("generated key :{} , has been update to github".format(key_title_adc))

    # Jenkins part
    #update existed jenkins key
    conf=server.get_credential_config(key_title,jenkins_project_folder)
    print("---original jenkins config---")
    print(conf)
    #new_xml_str=conf.replace("\n      <secret-redacted/>\n    ",private_key)
    try:
        root = ElementTree.fromstring(conf)
        privateKey = root.find('privateKeySource/privateKey')
        privateKey.remove(privateKey.find('secret-redacted'))
        privateKey.text = private_key
        root.find('description').text = key_title_adc
        new_xml_str = ElementTree.tostring(root, encoding='unicode', xml_declaration=False)
        print("---will be updated to---")
        print(new_xml_str)
        print("------------------------")
        reconf=server.reconfig_credential(jenkins_project_folder,new_xml_str)
        print("credential updated for jenkins:{}".format(key_title_adc))

    except Exception as e:
        print(e)
        print("Jenkins part not updated!")
       
    with open("./key_gen/{}.pub".format(key_title_adc),"w") as f:
        f.write(public_key)
    with open("./key_gen/{}".format(key_title_adc),"w") as f:
        f.write(private_key)





