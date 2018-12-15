# Magic Catalog App
A Flask based catalog app designed to allow users to create categories of products and list various items along with a description in that assigned category. The site is password protected using Google's oAuth functionality.

Each category item is visible to all users but only an owner of a given category or item can make changes to that category or item.

## Installation
In order to use the Magic Catalog App, you'll need to run it on a virtual machine or a live server. These installation instructions will discuss implementing the software in a virtual machine for the sake of simplicity. You'll need to install 3 programs to run the Magic Catalog App:

- Virtual Box
- Git
- Vagrant

This bundle will function as your virtual machine and enable you to run the app.

### Git
Download Git from [git-scm](https://git-scm.com/downloads). Install the appropriate version for your operating system. On a Windows machine, you will be provided with GitBash, a Unix style terminal. Use your standard terminal on a Linux or Mac machine.

### Virtual Box
The software which runs your virtual machine is Virtual Box. Download the software from [Virtualbox.org](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) and install the version appropriate for your operating system.

### Vagrant
Vagrant is the software which enables your virtual machine to communicate with your actual computer and share files between the two. Download Vagrant at [vagrantup.com](https://www.vagrantup.com/downloads.html) and install the version appropriate for your operating system.

**Note on Windows:** Vagrant might ask for a firewall exception, be sure to allow this. You may also have to enable virtual machine in your system's VIOS.

### Fetch Source Code and VM Configuration
Open a Terminal to download the source code

**Windows:** Use the GitBash program.

**Other Systems:** Use your favorite terminal.

#### Fork the Magic App Repository
Log into your personal GitHub account and fork the [MagicCatalogApp](https://github.com/VirgilAnderson/catalog). You can use this personal repository as a backup later.

#### Clone the remote on your local machine
From the terminal run the clone command to download the starter code to your machine. Make sure you replace ```<username>``` with your GitHub username.

Clone the repo with ```git clone http://github.com/<username>/catalog catalog```

This will give you a directory named catalog that is a clone of the Magic Catalog App repository.

#### Run the Virtual Machine
Using your terminal, use the ```cd catalog/vagrant``` (Change Directory) command to move to the vagrant directory of the catalog repository.

Enter the command ```vagrant up``` to launch your virtual machine.

Once your virtual machine is running, enter the ```vagrant ssh``` command to log your terminal into the virtual machine. To log out, you can type ```exit``` in the shell and to turn the machine off use the command ```vagrant halt```.

Once you've logged into your virtual machine, use the ```cd/vagrant``` command to move to the shared folder between your virtual machine and your host machine.

#### Running the Magic Catalog App
To run the Magic Catalog App, you'll first need to move to the catalog directory. Change directories with the ```cd catalog``` command.

Ensure you are in the correct directory with the ```ls``` command. You should see project.py, database_setup.py and two directories: 'static' and 'templates'.

##### Initialize the database
To create the database, you'll need to run the command ```python database_setup.py```

##### Initialize the app
Run the command ```python project.py``` to run the Flask server. In your browser visit **http://localhost:5000** to view the magic catalog app.

You should be able to create, read, update and delete categories and items.
