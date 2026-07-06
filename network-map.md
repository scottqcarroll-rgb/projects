# Home Network Map — 192.168.1.0/24

## Server (ClawZ840)
- **192.168.1.222** — clawz840 (Ubuntu 24.04, this server)
  - Services: SSH (22), HTTP (80), HTTPS (443), SMB (445/139), Docker
  - Tailscale: 100.124.71.12
  - SMB share: `\\192.168.1.222\projects` → /home/scott/projects

## Known Devices
| IP | Name | Notes |
|----|------|-------|
| 192.168.1.68 | truenas-scale | TrueNAS SCALE (Family NAS) |
| 192.168.1.88 | iPhone | Mobile device |
| 192.168.1.103 | RokuStreamingStick | Streaming stick |
| 192.168.1.104 | MyQ-E9F | Chamberlain garage door (IoT) |
| 192.168.1.106 | wlan0 | Unknown device |
| 192.168.1.108 | Linux.attlocal.net | Unknown Linux device |
| 192.168.1.114 | RokuUltra | Roku Ultra |
| 192.168.1.121 | Ring-c4a92f | Ring camera/doorbell |
| 192.168.1.135 | deco-M4R | Mesh router node |
| 192.168.1.137 | iPhone-13 | iPhone 13 |
| 192.168.1.141 | HP516D67 | HP printer (OfficeJet?) |
| 192.168.1.149 | My-ecobee | Ecobee smart thermostat |
| 192.168.1.152 | deco-M4R | Mesh router node |
| 192.168.1.158 | FLIR-PE133F-158 | FLIR camera, RTSP 554 |
| 192.168.1.163 | FLIR-PE133F-163 | FLIR camera, RTSP 554 |
| 192.168.1.184 | NPI0D1185 | HP MFP printer (M28w?) |
| 192.168.1.188 | Brother printer | Brother HL-L2370DW |
| 192.168.1.231 | HisenseRokuTV | Hisense Roku TV |
| 192.168.1.254 | dsldevice | Router/gateway (deco or ISP) |

## Unidentified
- 192.168.1.105
- 192.168.1.113
- 192.168.1.200
- 192.168.1.242

## How to Access SMB Share (from any Windows PC on LAN)
```
\\192.168.1.222\projects
Username: scott
Password: admin
```
No Tailscale needed — firewall is open to 192.168.1.0/24 for SMB.