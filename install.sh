cd ch341ser_linux/driver
make && sudo make install

sudo dmesg | grep tty # check if you can see the device port
sudo apt purge brltty

sudo cp 99-m2-rtk.rules /etc/udev/rules.d/99-m2-rtk.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
