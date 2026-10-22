# Backup Appliance Runbook — OpenEye OE-MT-Gen-2 ("backup01")

**Role:** dedicated, low-power, off-box backup target. Not a hypervisor.
**Host:** OpenEye OE-MT-Gen-2 — Intel i3, 16 GB DDR4, 256 GB SSD, 2× 4 TB drives, 2U.
**OS:** Debian 13.7 "trixie" (kernel 6.12 LTS), no desktop.
**Storage:** ZFS mirror of the two 4 TB drives, pool `tank`, ~3.6 TiB usable.
**Address:** `192.168.1.50` (verified unused at time of writing — set a DHCP reservation, not a hard-coded static IP).

## Topology

```
TrueNAS 192.168.1.68 ──ZFS send/recv over SSH──▶ backup01 : tank/truenas
Mac Studio .240      ──SMB (Time Machine)─────▶ backup01 : tank/mac/timemachine
Z840 .222            ──restic over SFTP───────▶ backup01 : tank/restic/z840
```

## Data budget

| Source | Path | Size |
|---|---|---|
| TrueNAS | `Family/FamilyShare` | 467 GB |
| TrueNAS | `Family/immich` | 29 GB |
| TrueNAS | `Family/Media` (replaceable) | 2.21 TB |
| Z840 | projects, configs, Docker volumes | ~20 GB |
| Mac Studio | photos, docs (models excluded) | ~10 GB |
| **Total** | | **~2.72 TB** |

On a ~3.6 TiB mirror that leaves roughly **1 TiB for snapshots and growth**. If it gets tight, drop `Family/Media` from replication first — it is the only bulk that can be re-acquired.

---

## 1. Install Debian 13.7

1. Write the **amd64 netinst** image for 13.7 to USB; boot the appliance.
2. BIOS first: **disable Secure Boot** (DKMS ZFS modules are unsigned), confirm AHCI, set "power on after AC loss".
3. Installer choices:
   - Hostname `backup01`, domain `local`.
   - Root password + one admin user (`scott`).
   - Guided partitioning, **entire 256 GB SSD**, **ext4** (keep the OS boring), 2 GB swap.
   - Tasksel: **SSH server** + **standard system utilities** only. **No desktop.**
4. First boot:

```bash
apt update && apt full-upgrade -y
apt install -y sudo vim curl htop smartmontools chrony unattended-upgrades \
               linux-headers-amd64 samba restic avahi-daemon
```

5. Enable backports and install ZFS from them (Debian's own ZFS wiki recommends backports):

```bash
. /etc/os-release
echo "deb http://deb.debian.org/debian ${VERSION_CODENAME}-backports main contrib" \
  > /etc/apt/sources.list.d/backports.list
apt update
apt -t trixie-backports install -y zfs-dkms zfsutils-linux
```

6. Cap ARC — 16 GB total means don't let ZFS eat it all:

```bash
echo 'options zfs zfs_arc_max=4294967296' > /etc/modprobe.d/zfs.conf   # 4 GiB
update-initramfs -u -k all
```

---

## 2. Create the ZFS mirror

Use **`/dev/disk/by-id/`** paths, never `sdX` — USB and SATA enumeration already changed on TrueNAS once (`sda` → `sdh`).

```bash
ls -l /dev/disk/by-id/ | grep -E 'ata-|wwn-'
```

```bash
zpool create -o ashift=12 \
  -O compression=lz4 -O atime=off -O xattr=sa -O acltype=posixacl \
  tank mirror \
  /dev/disk/by-id/ata-DISK1_SERIAL \
  /dev/disk/by-id/ata-DISK2_SERIAL
```

```bash
zfs create tank/truenas
zfs create tank/z840
zfs create tank/mac
zfs create tank/mac/timemachine
zfs create tank/restic
zfs create tank/restic/z840

# Keep each consumer inside its lane
zfs set quota=3T   tank/truenas
zfs set quota=400G tank/mac
zfs set quota=100G tank/restic
zfs set snapdir=visible tank/truenas
```

Verify: `zpool status -v tank` should show a healthy two-disk mirror.

---

## 3. TrueNAS → backup01 replication (the important one)

### 3.1 Authorize the TrueNAS key on backup01

On **backup01** as root:

```bash
install -d -m 700 /root/.ssh
# Paste the public key from TrueNAS (Credentials → Backup Credentials → SSH Keypairs)
echo 'ssh-ed25519 AAAA... truenas-replication' >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
```

```bash
cat >/etc/ssh/sshd_config.d/10-replication.conf <<'EOF'
PermitRootLogin prohibit-password
EOF
systemctl restart ssh
```

### 3.2 Build the task in TrueNAS

1. **Credentials → Backup Credentials → SSH Keypairs** → generate.
2. **SSH Connections** → add: host `192.168.1.50`, user `root`, key from above. Test it.
3. **Data Protection → Replication Tasks → Add:**
   - Source: *On this System*, dataset `Family/FamilyShare` (repeat for `Family/immich`; add `Family/Media` if room).
   - Destination: *On a Different System*, the SSH connection, target `tank/truenas/familyshare` etc.
   - Recursive: on. Use existing `auto-*` snapshots. Schedule hourly or daily.
   - Encryption: off (LAN, already at rest on your terms).
   - Enable snapshot retention on the destination, but **keep it conservative** — the source already owns the schedule.

### 3.3 Snapshot state (verified on TrueNAS, 2026-10-22)

| Task | Dataset | Schedule | Retention | Note |
|---|---|---|---|---|
| daily | `Family` (recursive) | `0 0 * * *` | 5 days | covers FamilyShare + immich |
| monthly | `Family` (recursive) | `0 0 1 * *` | 2 months | |
| "hourly" | `Family` | `0 0 * * *` | 3 days | **misnamed — actually daily** |
| weekly | `Family/FamilyShare` | `0 0 * * sun` | 2 weeks | |
| "monthly" | `Family/FamilyShare` | `0 0 1 * mon` | 2 weeks | first Monday |

**Gotcha:** the task labelled *hourly* runs daily. If you want hourly RPO, fix that schedule before relying on it.

There are **no** snapshot tasks for `Galaxy`, `Vault`, or `Vault5tb`.

---

## 4. Mac Studio Time Machine

On **backup01**:

```bash
groupadd -g 3000 timemachine
useradd -M -s /usr/sbin/nologin -G timemachine tmbackup
chown -R tmbackup:timemachine /tank/mac/timemachine
smbpasswd -a tmbackup          # set a strong, unique password
```

`/etc/samba/smb.conf`:

```ini
[global]
   server role = standalone server
   workgroup = WORKGROUP
   server string = backup01
   # NOTE: fruit:aapl is deprecated/ignored in Samba 4.22 — omit it.
   vfs objects = fruit streams_xattr
   fruit:metadata = stream
   fruit:model = MacSamba
   fruit:posix_rename = yes
   fruit:veto_appledouble = no
   fruit:nfs_aces = no
   fruit:wipe_intentionally_left_blank_rfork = yes
   fruit:delete_empty_adfiles = yes

[TimeMachine]
   path = /tank/mac/timemachine
   valid users = tmbackup
   browseable = yes
   read only = no
   vfs objects = fruit streams_xattr
   fruit:time machine = yes
   fruit:time machine max size = 400G
```

```bash
testparm -s
systemctl enable --now smbd avahi-daemon
```

On the **Mac Studio**:

```bash
for d in ~/.ollama ~/LLMs ~/ComfyUI ~/models; do tmutil addexclusion "$d"; done
tmutil setdestination -a smb://tmbackup@192.168.1.50/TimeMachine
tmutil startbackup --auto
```

Excluded ~185 GB of re-downloadable model weights; the ~1 GB of photos and documents is what actually matters.

---

## 5. Z840 → restic over SFTP

### 5.1 On backup01

```bash
useradd -m -d /tank/restic/z840 -s /bin/bash backup
mkdir -p /tank/restic/z840/.ssh && chmod 700 /tank/restic/z840/.ssh
# Paste the Z840 restic public key:
echo 'ssh-ed25519 AAAA... restic-z840' > /tank/restic/z840/.ssh/authorized_keys
chmod 600 /tank/restic/z840/.ssh/authorized_keys
chown -R backup:backup /tank/restic/z840
```

### 5.2 On the Z840

```bash
sudo apt install -y restic
sudo install -d -m 700 /etc/restic
# Store the repo password in your password manager too — do not let this be the only copy.
sudo sh -c 'head -c 32 /dev/urandom | base64 > /etc/restic/pass && chmod 600 /etc/restic/pass'
sudo ssh-keygen -t ed25519 -N '' -f /root/.ssh/id_ed25519_restic
# Add /root/.ssh/id_ed25519_restic.pub to backup01 per 5.1, then:
sudo RESTIC_REPOSITORY='sftp:backup@192.168.1.50:/tank/restic/z840' \
     RESTIC_PASSWORD_FILE=/etc/restic/pass restic init
```

`/usr/local/bin/restic-z840.sh`:

```bash
#!/bin/bash
set -euo pipefail
export RESTIC_REPOSITORY='sftp:backup@192.168.1.50:/tank/restic/z840'
export RESTIC_PASSWORD_FILE=/etc/restic/pass

restic backup \
  /home/scott/projects \
  /home/scott/.config \
  /home/scott/.hermes \
  /var/lib/docker/volumes \
  --exclude-caches \
  --exclude '/home/scott/.hermes/venvs' \
  --exclude '/home/scott/.hermes/hermes-agent' \
  --exclude '/home/scott/.cache' \
  --exclude '/home/scott/.npm' \
  --exclude '**/node_modules' \
  --exclude '**/__pycache__' \
  --exclude '**/venv' \
  --tag z840

restic forget --tag z840 --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune
```

`/etc/systemd/system/restic-z840.service`:

```ini
[Unit]
Description=Restic backup to backup01
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/restic-z840.sh
Nice=10
IOSchedulingClass=idle
```

`/etc/systemd/system/restic-z840.timer`:

```ini
[Unit]
Description=Nightly restic backup to backup01

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
```

```bash
sudo chmod +x /usr/local/bin/restic-z840.sh
sudo systemctl daemon-reload
sudo systemctl enable --now restic-z840.timer
```

**Note:** backing up live Docker volumes is only crash-consistent. For the handful that matter (Open WebUI, etc.), stop the container or run an application-level dump first.

---

## 6. Verification

```bash
# appliance
zpool status -v tank
zfs list -o name,used,avail,quota
zfs list -t snapshot -o name,used,refer -s creation | tail -20
smartctl -a /dev/sdX

# TrueNAS
# Data Protection → Replication Tasks → check last run + bytes
curl -sk -H "Authorization: Bearer $TRUENAS_API_KEY" \
  "https://192.168.1.68/api/v2.0/replication" | jq '.[] | {name, state, last_run}'

# Z840
sudo restic snapshots
sudo restic check
```

A backup is not real until you restore from it. Once a month, pull one file from each source:

```bash
sudo restic restore latest --target /tmp/restore --include /home/scott/projects/network-map.md
# TrueNAS file:
zfs get snapdir tank/truenas/familyshare   # then browse /tank/truenas/familyshare/.zfs/snapshot/
```

Enable monthly scrubs:

```bash
systemctl enable --now zfs-scrub-monthly@tank.timer
```

---

## 7. Recovery

| Failure | Action |
|---|---|
| Single file deleted on TrueNAS | Read it from the replicated snapshot on backup01 (`.zfs/snapshot/…`) |
| Whole dataset lost on TrueNAS | `zfs send tank/truenas/familyshare@snap \| ssh truenas zfs recv -F Family/FamilyShare` |
| Z840 host lost | `restic restore latest --target /mnt/restore` then copy back |
| Mac lost | Standard macOS Migration Assistant from the Time Machine share |
| One mirror disk dies | `zpool replace tank /dev/disk/by-id/OLD /dev/disk/by-id/NEW`; runs `resilver` |

---

## 8. Findings and gotchas (from the 2026-10-22 TrueNAS audit)

1. **`Vault5tb` is SUSPENDED and is a single USB disk** — model `Backup+_Hub_BK`, serial `NA8T9DNT`, device `sdh`. No redundancy, and USB is exactly why it dropped. Recover with:
   ```bash
   zpool clear Vault5tb && zpool status Vault5tb && zpool scrub Vault5tb
   ```
   If it re-suspends, the enclosure/cable/drive is failing — copy the 247 GB off and retire it. **Do not treat this pool as a backup.**
2. **TrueNAS currently has zero replication tasks and zero cloud-sync jobs.** Until section 3 is done, the 2.74 TB on `Family` exists in exactly one place.
3. **The snapshot task named "hourly" runs daily** (`0 0 * * *`). Fix if you want an hourly RPO.
4. **`FamilyShare` has only weekly/monthly dataset-level snapshots**, but the recursive `Family` daily covers it. Fine for daily replication; not for hourly.
5. **TrueNAS REST API is deprecated** (removal in 26.04). The dashboard on `.222` is polling it **408×/24 h**. Plan the move to JSON-RPC 2.0 over WebSocket.
6. **Secure Boot must stay off** on backup01 — DKMS ZFS modules are unsigned.
7. **Always use `/dev/disk/by-id/`** — the USB device already renumbered (`sda` → `sdh`) between boots.
8. Five TrueNAS apps and a system update are pending; do them *after* the first successful off-box copy, not before.
9. **Exclude model weights** from every job: `~/.ollama` (101 GB), `~/ComfyUI` (36 GB), `~/LLMs` (29 GB), `~/models` (19 GB). That is ~185 GB of re-downloadable data.

---

## 9. Order of operations

1. Recover or retire `Vault5tb` (section 8.1).
2. Install Debian 13.7 + ZFS mirror (sections 1–2).
3. TrueNAS replication for `FamilyShare` + `immich` (section 3) — **first win, ~500 GB protected**.
4. Mac Time Machine (section 4).
5. Z840 restic (section 5).
6. Add `Family/Media` if capacity allows.
7. Verify a restore end-to-end (section 6).
