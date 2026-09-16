# Ctronics C6F0SpZ0N0PpL2 — full CGI API

Extracted from the source of the camera's own web interface
(model C6F0SpZ0N0PpL2, firmware V30.1.60.11.88), which it serves from
`/web/`. Each settings page loads its current values through a
`<script src="param.cgi?cmd=get...">` tag and saves them by POSTing a hidden
form to `param.cgi` — so the read command, the write command and every
parameter name below come from the camera itself, not from guesswork.

Base URL: `http://<ip>/web/cgi-bin/hi3510/param.cgi`
Auth: HTTP Basic. Reads answer with `var key="value";` lines, writes with
`[Succeed]` / `[Error]`. Every parameter carries a leading dash.

## PTZ (not a param.cgi command)

    ptzctrl.cgi?-step=0&-act=<action>&-speed=<1-8>

`-act`: `up` `down` `left` `right` `home` `stop` `zoomin` `zoomout`
`focusin` `focusout` `hscan` `vscan`

Movement runs while the action is active; the interface sends `stop` on
mouse-up. `home`, `hscan` and `vscan` are sent without a following stop.

`zoomin`, `zoomout`, `focusin` and `focusout` are accepted by the firmware
on every model, but only do something on a camera with a varifocal lens. The
C6F0SpZ0N0PpL2 has a fixed lens, so they are silently ignored there.
`getcapability` does not report this — it only carries `cap_cvbs`.

## Presets

    param.cgi?cmd=preset&-act=set &-status=1&-number=<0-63>   save
    param.cgi?cmd=preset&-act=goto&-status=1&-number=<0-63>   recall
    param.cgi?cmd=preset&-act=set &-status=0&-number=<0-63>   delete

Zero-based: the interface computes `form_preset.value - 1`, so its
"Voreinstellung 1" is `-number=0`.

**64 slots**, established by testing on the device — 64 works, 65 does not.
The page's preset field is a free text input (`maxlength="3"`) with no
validation in its JavaScript. The 1-8 dropdown elsewhere in the interface
belongs to `setmotorattr -alarmpresetindex` ("drive to preset N on alarm"),
which is a separate feature and really is limited to 8.

## Still images (plain HTTP, no CGI)

    /tmpfs/auto.jpg   self-refreshing snapshot
    /tmpfs/snap.jpg   capture a frame now

---

# Per-page inventory


## /web/485set.html

Lesen: `getptzcomattr`

Schreiben: `cmd=setptzcomattr` → `-address` `-protocal` `-speed` `-baud` `-databit` `-stopbit` `-check`

## /web/addport.html

Lesen: `getdevices`

Schreiben: `cmd=setdevices` → `-dev1_number` `-dev1_clear` `-dev1_host` `-dev1_alias` `-dev1_port` `-dev1_user` `-dev1_pwd`

Schreiben: `cmd=setdevices` → `-dev2_number` `-dev2_clear` `-dev2_host` `-dev2_alias` `-dev2_port` `-dev2_user` `-dev2_pwd`

Schreiben: `cmd=setdevices` → `-dev3_number` `-dev3_clear` `-dev3_host` `-dev3_alias` `-dev3_port` `-dev3_user` `-dev3_pwd`

Schreiben: `cmd=setdevices` → `-dev4_number` `-dev4_clear` `-dev4_host` `-dev4_alias` `-dev4_port` `-dev4_user` `-dev4_pwd`

Schreiben: `cmd=setdevices` → `-dev5_number` `-dev5_clear` `-dev5_host` `-dev5_alias` `-dev5_port` `-dev5_user` `-dev5_pwd`

Schreiben: `cmd=setdevices` → `-dev6_number` `-dev6_clear` `-dev6_host` `-dev6_alias` `-dev6_port` `-dev6_user` `-dev6_pwd`

Schreiben: `cmd=setdevices` → `-dev7_number` `-dev7_clear` `-dev7_host` `-dev7_alias` `-dev7_port` `-dev7_user` `-dev7_pwd`

Schreiben: `cmd=setdevices` → `-dev8_number` `-dev8_clear` `-dev8_host` `-dev8_alias` `-dev8_port` `-dev8_user` `-dev8_pwd`

## /web/alarm.html

Lesen: `getmdalarm`, `getrelayattr`, `getalarmsnapattr`, `getmotorattr`, `getalarmsoundattr`, `getaudioflag`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setrelayattr` → `-time`

Schreiben: `cmd=setalarmsnapattr` → `-snap_count`

Schreiben: `cmd=setmotorattr` → `-alarmpresetindex`

Schreiben: `cmd=setalarmsoundattr` → `-sound_type` `-sound_time`

## /web/alarmaudio.html

Lesen: `getaudioalarmattr`

Schreiben: `cmd=setaudioalarmattr` → `-aa_enable` `-aa_value`

## /web/alarmin.html

Lesen: `getioattr`

Schreiben: `cmd=setioattr` → `-io_enable` `-io_flag`

## /web/alarmsmd.html

Lesen: `getsmdattr`, `getsmdex`, `getmdalarm`

Schreiben: `cmd=setmdalarm` → `-aname` `-switch`

Schreiben: `cmd=setsmdattr` → `-smd_enable`

Schreiben: `cmd=setsmdex` → `-smd_rect` `-smd_gthresh` `-smd_type`

## /web/amazon.html

Lesen: `getamazonattr`

Schreiben: `cmd=setamazonattr` → `-amazon_enable`

## /web/audio.html

Lesen: `getaencattr`, `getaudioinvolume`, `getaudiooutvolume`

Schreiben: `cmd=setaencattr` → `-chn` `-aeswitch`

Schreiben: `cmd=setaencattr` → `-chn` `-aeformat`

Schreiben: `cmd=setaencattr` → `-chn` `-aeswitch`

Schreiben: `cmd=setaencattr` → `-chn` `-aeformat`

Schreiben: `cmd=setaudioinvolume` → `-volume` `-volin_type`

Schreiben: `cmd=setaudiooutvolume` → `-volume`

## /web/autosnapex.html

Lesen: `getsnaptimerattrex`, `getscheduleex`, `getaudioflag`

Schreiben: `cmd=setsnaptimerattrex` → `-as_interval` `-as_type` `-as_enable`

Schreiben: `cmd=setsnaptimerattrex` → `-as_interval` `-as_type` `-as_enable`

Schreiben: `cmd=setsnaptimerattrex` → `-as_interval` `-as_type` `-as_enable`

Schreiben: `cmd=setscheduleex` → `-ename` `-week0` `-week1` `-week2` `-week3` `-week4` `-week5` `-week6`

## /web/backplay.html

Lesen: `getsetupflag`

## /web/chkframe.html

Lesen: `getchkwireless`

## /web/cloud.html

Lesen: `getcloudenable`

Schreiben: `cmd=setcloudenable` → `-cloud_enable`

## /web/ddns.html

Lesen: `getourddnsattr`, `getupnpattr`, `get3thddnsattr`

Schreiben: `cmd=setupnpattr` → `-upm_enable`

Schreiben: `cmd=set3thddnsattr` → `-d3th_enable` `-d3th_service` `-d3th_uname` `-d3th_passwd` `-d3th_domain`

Schreiben: `cmd=setourddnsattr` → `-our_enable` `-our_port` `-our_uname` `-our_passwd` `-our_server` `-our_domain`

## /web/deviceinfo.html

Lesen: `getserverinfo`, `getnetattr`, `getstreamnum`, `getourddnsattr`, `get3thddnsattr`, `getaudioflag`, `getdevtype`, `getossattr`

## /web/display.html

Lesen: `getvideoattr`, `getimageattr`, `getsetupflag`, `getimagemaxsize`, `getaudioflag`, `getserverinfo`, `getircutattr`, `getinfrared`, `getrtmpattr`, `gethttpport`, `setimageattr`

Schreiben: `cmd=setinfrared` → `-infraredstat`

Schreiben: `cmd=setircutattr` → `-saradc_switch_value`

Schreiben: `cmd=setimageattr` → `-bright` `-contrast` `-saturation` `-sharpness` `-mirror` `-flip` `-shutter` `-night` `-wdr` `-wdrvalue` `-noise` `-gc` `-ae` `-targety` `-aemode` `-image_type` `-imgmode`

## /web/email.html

Lesen: `getsmtpattr`

Schreiben: `cmd=setsmtpattr` → `-ma_server` `-ma_from` `-ma_to` `-ma_subject` `-ma_text` `-ma_logintype` `-ma_username` `-ma_password` `-ma_port` `-ma_ssl`

## /web/ftp.html

Lesen: `getftpattr`

Schreiben: `cmd=setftpattr` → `-ft_server` `-ft_port` `-ft_username` `-ft_password` `-ft_mode` `-ft_dirname` `-ft_autocreatedir`

## /web/g4.html

Lesen: `get4gattr`

Schreiben: `cmd=set4gattr` → `-g4_runmode` `-g4_apn` `-g4_authtype` `-g4_username` `-g4_password`

## /web/gb28181.html

Lesen: `getgb28181attr`

Schreiben: `cmd=setgb28181attr` → `-gb_enable` `-gb_svrid` `-gb_svrip` `-gb_svrport` `-gb_devid` `-gb_devport` `-gb_devpwd` `-gb_alarmid` `-gb_heartcycle` `-gb_heartcount` `-gb_regtime` `-gb_audioenable` `-gb_audiotype` `-gb_videochn`

## /web/hiplatform.html

Lesen: `gethip2pattr`

Schreiben: `cmd=sethip2pattr` → `-hip2p_enable`

## /web/initializemain.html

Lesen: `getcapability`, `getmotorrange`

Schreiben: `cmd=setcapability` → `-cap_cvbs`

Schreiben: `cmd=sysreboot` → 

Schreiben: `cmd=sysreset` → 

Schreiben: `cmd=setlanguage` → `-lancode`

Schreiben: `cmd=setmotorrange` → `-lenstype`

## /web/interip.html

Lesen: `getinterip`

## /web/mainpage.html

Lesen: `getvideoattr`, `getvencattr`, `getsetupflag`, `getaudioflag`, `getrtmpattr`, `gethttpport`, `getwebattr`, `setwebattr`, `preset`

## /web/mainpage4.html

Lesen: `getvencattr`, `getsetupflag`, `getdevices`, `preset`

## /web/mainpage9.html

Lesen: `getvencattr`, `getsetupflag`, `getdevices`, `preset`

## /web/md.html

Lesen: `getvideoattr`, `getmdattr`, `getsetupflag`, `getaudioflag`

Schreiben: `cmd=setmdattr` → `-name0` `-x0` `-y0` `-w0` `-h0` `-s0` `-t0` `-enable0` `-chn0`

Schreiben: `cmd=setmdattr` → `-name1` `-x1` `-y1` `-w1` `-h1` `-s1` `-t1` `-enable1` `-chn1`

Schreiben: `cmd=setmdattr` → `-name2` `-x2` `-y2` `-w2` `-h2` `-s2` `-t2` `-enable2` `-chn2`

Schreiben: `cmd=setmdattr` → `-name3` `-x3` `-y3` `-w3` `-h3` `-s3` `-t3` `-enable3` `-chn3`

Schreiben: `cmd=setmdattr` → `-name` `-x` `-y` `-w` `-h` `-s` `-t` `-enable` `-chn`

Schreiben: `cmd=setmdattr` → `-name1` `-enable1` `-chn1`

Schreiben: `cmd=setmdattr` → `-name2` `-enable2` `-chn2`

Schreiben: `cmd=setmdattr` → `-name3` `-enable3` `-chn3`

## /web/menu.html

Lesen: `getvencattr`, `getsetupflag`, `getaudioflag`, `getplatformtype`

## /web/network.html

Lesen: `getnetattr`, `gethttpport`, `getrtspport`, `getrtspauth`, `getrtmpattr`

Schreiben: `cmd=setnetattr` → `-ipaddr` `-netmask` `-gateway` `-dhcp` `-dnsstat` `-fdnsip` `-sdnsip`

Schreiben: `cmd=setrtspauth` → `-rtsp_aenable`

Schreiben: `cmd=setrtspport` → `-rtspport`

Schreiben: `cmd=setrtmpattr` → `-rtmpport`

Schreiben: `cmd=sethttpport` → `-httpport`

## /web/onvif.html

Lesen: `getonvifattr`

Schreiben: `cmd=setonvifattr` → `-ov_enable` `-ov_port` `-ov_authflag` `-ov_forbitset` `-ov_subchn` `-ov_snapchn` `-ov_nvctype`

## /web/oplatform.html

Lesen: `getoplatformattr`

Schreiben: `cmd=setoplatformattr` → `-op_enable` `-op_uname` `-op_passwd` `-op_server` `-op_port` `-op_timeout`

## /web/osd.html

Lesen: `getoverlayattr`, `getvencattr`

Schreiben: `cmd=setoverlayattr` → `-region` `-show` `-place`

Schreiben: `cmd=setoverlayattr` → `-region` `-show` `-name` `-place`

Schreiben: `cmd=setoverlayattr` → `-region` `-show`

## /web/record.html

Lesen: `getplanrecattr`, `getscheduleex`

Schreiben: `cmd=setplanrecattr` → `-planrec_enable` `-planrec_chn` `-planrec_time`

Schreiben: `cmd=setscheduleex` → `-ename` `-week0` `-week1` `-week2` `-week3` `-week4` `-week5` `-week6`

## /web/restarttime.html

Lesen: `gettimerreboot`

Schreiben: `cmd=settimerreboot` → `-sr_enable` `-sr_day` `-sr_hour`

## /web/scan.html

Lesen: `searchwireless`

## /web/scheduleex.html

Lesen: `getscheduleex`

Schreiben: `cmd=setplanrecattr` → `-recswitch` `-recstream` `-planrec_time`

Schreiben: `cmd=setscheduleex` → `-ename` `-week0` `-week1` `-week2` `-week3` `-week4` `-week5` `-week6`

## /web/systemlog.html

Schreiben: `cmd=cleanlog` → `-name`

## /web/terminal.html

Lesen: `getmotorattr`, `getsmartrackattr`, `getlightattr`

Schreiben: `cmd=setmotorattr` → `-tiltscan` `-tiltspeed` `-panscan` `-panspeed` `-movehome` `-ptzalarmmask`

Schreiben: `cmd=setsmartrackattr` → `-smartrack_enable`

Schreiben: `cmd=setlightattr` → `-light_enable`

## /web/test_ftp.html

Lesen: `testftp`

## /web/test_smtp.html

Lesen: `testsmtp`

## /web/time.html

Lesen: `getservertime`, `getntpattr`

Schreiben: `cmd=setntpattr` → `-ntpenable` `-ntpserver` `-ntpinterval`

Schreiben: `cmd=setservertime` → `-timezone` `-dstmode`

Schreiben: `cmd=setservertime` → `-stime` `-timezone` `-dstmode`

Schreiben: `cmd=setntpattr` → `-ntpenable`

## /web/tmall.html

Lesen: `gettmallattr`

Schreiben: `cmd=settmallattr` → `-tmall_enable`

## /web/user.html

Lesen: `getuserattr`

Schreiben: `cmd=setuserattr` → `-at_username` `-at_newname` `-at_password`

Schreiben: `cmd=setuserattr` → `-at_username` `-at_newname` `-at_password`

Schreiben: `cmd=setuserattr` → `-at_username` `-at_newname` `-at_password`

## /web/video.html

Lesen: `getvencattr`, `getvideoattr`, `getimagemaxsize`, `getmobilesnapattr`, `getserverinfo`

Schreiben: `cmd=setvideoattr` → `-videomode` `-vinorm` `-profile`

Schreiben: `cmd=setvencattr` → `-chn` `-bps` `-fps` `-brmode` `-imagegrade` `-gop`

Schreiben: `cmd=setvencattr` → `-chn` `-bps` `-fps` `-brmode` `-imagegrade` `-gop`

## /web/videoshade.html

Lesen: `getvideoattr`, `getcover`, `getsetupflag`

Schreiben: `cmd=setcover` → `-name0` `-enable0` `-color0` `-x0` `-y0` `-w0` `-h0`

Schreiben: `cmd=setcover` → `-name1` `-enable1` `-color1` `-x1` `-y1` `-w1` `-h1`

Schreiben: `cmd=setcover` → `-name2` `-enable2` `-color2` `-x2` `-y2` `-w2` `-h2`

Schreiben: `cmd=setcover` → `-name3` `-enable3` `-color3` `-x3` `-y3` `-w3` `-h3`

## /web/wifi.html

Lesen: `getwirelessattr`, `getnetattr`

Schreiben: `cmd=setwirelessattr` → `-ssid` `-wifistatus` `-wifimode` `-encryption` `-enable` `-key`

Schreiben: `cmd=chkwirelessattr` → `-key` `-ssid` `-wifistatus` `-wifimode` `-encryption`

## /web/wifimodel.html

Lesen: `getwifiattrex`

Schreiben: `cmd=setwifiattrex` → `-wf_mode` `-wf_speed` `-wf_chn` `-wf_power`

## /web/xqplatform.html

Lesen: `getxqp2pattr`

Schreiben: `cmd=setxqp2pattr` → `-xqp2p_enable`
