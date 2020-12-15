import win32com.client

outlook=win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

# list email address linked to account
i = 0
email_addresses = []
while True:
    try:
        folder_name = outlook.Folders[i].Name
        print(folder_name)
        email_addresses.append(folder_name)
        i += 1
    except:
        print("no more email addresses")
        break
print(email_addresses)

# inbox
email_address = outlook.Folders[1]
inbox = email_address.Folders("Inbox")
print(inbox.Name)

# subfolders under inbox
i = 0
inbox_subfolders = []
while True:
    try:
        print(i)
        subfolder_name = inbox.Folders[i].Name
        print(subfolder_name)
        inbox_subfolders.append(subfolder_name)
        i += 1
    except:
        print("no more subfolders")
        break
print(inbox_subfolders)

# ASDA receipt folder
target_folder = inbox.Folders("ASDA Order Receipts")

print(target_folder.Name)

# List items in folder
messages = target_folder.Items

body = messages[0].Body
print(type(body))

body = body.replace('\t', '\n')
lines = body.splitlines()

for i, line in enumerate(lines):
    print(i, line)