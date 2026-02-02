#
# Vagrantfile to create PXL Labs
#
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "almalinux/9"
  GROUP = "/pxl-lab"
  MEMORY = 1024

  # set host sync folder /vagrant to current directory
  config.vm.synced_folder '.', '/vagrant', disabled: true

  # ssh key config - re-use existing key
  config.ssh.forward_agent = true
  config.ssh.insert_key = false
  config.ssh.private_key_path = "~/.vagrant.d/insecure_private_key"

  # define VM configurations
  servers = [
    {name: "server0", ip: "192.168.56.100", port: 8888},
    {name: "server1", ip: "192.168.56.101", port: 8889}
  ]

  # create a group for the virtualbox machines
  config.vm.provider :virtualbox do |vb|
    vb.memory = MEMORY
    vb.customize ["modifyvm", :id, "--groups", GROUP] unless GROUP.nil?
  end

  # Define all servers in a loop
  servers.each do |server|
    config.vm.define server[:name] do |srv|
      srv.vm.hostname = "#{server[:name]}.pxldemo.local"
      srv.vm.network "private_network", ip: server[:ip]
      srv.vm.network "forwarded_port", guest: 80, host: server[:port]

      # Common /etc/hosts provisioning
      srv.vm.provision "shell", inline: <<-SHELL
        echo "#{servers.map { |s| "#{s[:ip]} #{s[:name]} #{s[:name]}.pxldemo.local" }.join("\n")}" | sudo tee -a /etc/hosts
      SHELL
    end
  end

  config.vm.post_up_message = "PXL Lab machine build complete."
end
