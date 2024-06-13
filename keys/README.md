Place your SSH private key(s) in this directory,
then set `ansible_ssh_private_key_file=keys/<filename>` in the `inventory` file,
on the line corresponding to the server which that key accesses.

Use the `inventory.sample` file as reference.

> [!NOTE]
> All files in this `keys/` directory (except for this `README.md` file)
> are listed in the `.gitignore` file, so they won't be committed to the repository.
