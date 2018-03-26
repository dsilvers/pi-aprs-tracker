sudo pip install -r requirements.txt

sudo cp tracker.service /etc/systemd/system/
sudo systemctl enable tracker
sudo systemctl start tracker