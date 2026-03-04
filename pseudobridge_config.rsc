# feb/26/2026 14:24:48 by RouterOS 6.49.19
# software id = LA4R-4J7D
#
# model = RouterBOARD cAP L-2nD
# serial number = 792E099C67FD
/interface bridge
add name=bridge-lan
/interface wireless security-profiles
set [ find default=yes ] supplicant-identity=MikroTik
add authentication-types=wpa2-psk mode=dynamic-keys name=home_pass \
    supplicant-identity=MikroTik wpa2-pre-shared-key=donntu1921
/interface wireless
set [ find default-name=wlan1 ] antenna-gain=0 band=2ghz-b/g/n channel-width=\
    20/40mhz-XX country=no_country_set disabled=no frequency=auto \
    frequency-mode=manual-txpower mode=station-pseudobridge security-profile=\
    home_pass ssid=DonNTU_Lecturer station-roaming=enabled
/user group
set full policy="local,telnet,ssh,ftp,reboot,read,write,policy,test,winbox,pas\
    sword,web,sniff,sensitive,api,romon,dude,tikapp"
/interface bridge port
add bridge=bridge-lan interface=ether1
add bridge=bridge-lan interface=wlan1
/ip neighbor discovery-settings
set discover-interface-list=!dynamic
/ip dhcp-client
add disabled=no interface=bridge-lan
/system clock
set time-zone-name=Europe/Kyiv
