import win32com.client
outlook = win32com.client.Dispatch("outlook.Application").GetNamespace('MAPI')
folder = outlook.Folders[1]
print(folder.Count)
