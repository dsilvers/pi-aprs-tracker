sudo pip install -r requirements.txt

sudo cp tracker.service /etc/systemd/system/
sudo systemd enable tracker
sudo systemd start tracker