# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.synced_folder ".", "/vagrant", type: "nfs"

  config.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
      vb.cpus   = 1
  end

  config.vm.network "private_network", ip: "192.168.59.105"
end
