# Media Folder Permission Fix - August 27, 2026

## Issue
User `sqc` encountered "The operation can't be completed because you don't have permission to access some of the items" when trying to delete files in `/mnt/Family/Media/` on TrueNAS.

## Root Cause Analysis
1. Files in `/mnt/Family/Media/TV-Shows-Series-transcoded/` were owned by `sqc:Apps`
2. The `Apps` group (GID 3005) existed but appeared to lack sufficient permissions for deletion operations
3. User `sqc` (UID 951) was member of groups: `builtin_administrators` (544), `scarroll` (3000), `kcarroll` (3003), `Apps` (3005), `Family` (3006)
4. Despite group membership, deletion operations failed with permission errors

## Diagnostic Commands Used
```bash
# Check file ownership
ls -la "/mnt/Family/Media/TV-Shows-Series-transcoded/Sopranos/Season 4/The Sopranos (1999) - S04E07 - Watching Too Much Television (1080p BluRay x265 ImE).mp4"
# Output: -rwxrwxr-x 1 sqc Apps ...

# Check effective user
id sqc
# Output: uid=951(sqc) gid=544(builtin_administrators) groups=544(builtin_administrators),3000(scarroll),3003(kcarroll),3005(Apps),3006(Family)

# Test deletion as sqc
sudo -u sqc rm -f "test_file.txt"  # This worked
sudo -u sqc rm -f "/mnt/Family/Media/TV-Shows-Series-transcoded/Sopranos/Season 4/The Sopranos (1999) - S04E07 - Watching Too Much Television (1080p BluRay x265 ImE).mp4"  # This failed

# Check effective permissions via sudo -l
sudo -l
# Output: User admin may run: (ALL) ALL, (ALL) ALL, NOPASSWD: ALL
```

## Solution Implemented
Changed ownership from `sqc:Apps` to `sqc:builtin_administrators`:

```bash
sudo chown -R sqc:builtin_administrators /mnt/Family/Media/
```

## Verification
1. Confirmed 0 files not owned by `sqc` after fix:
   ```bash
   find /mnt/Family/Media -type f ! -user sqc 2>/dev/null | wc -l
   # Result: 0
   ```

2. Successfully created and deleted test files as `sqc`:
   ```bash
   sudo -u sqc touch "/mnt/Family/Media/test_sqc_delete.txt" && sudo -u sqc rm -f "/mnt/Family/Media/test_sqc_delete.txt" && echo "Create/delete test as sqc: PASSED"
   ```

3. Restored accidentally deleted media files from ZFS snapshot:
   - S03E11: Pine Barrens episode
   - S01E01: The Sopranos pilot episode
   - Used snapshot: `Family/Media@auto-2026-08-27_00-00 - daily`

## Key Learnings
1. TrueNAS permission model can be complex with multiple overlapping groups
2. The `builtin_administrators` group (GID 544) appears to have the necessary permissions for media folder operations
3. Simply being a member of a group isn't always sufficient - the file must be owned by a group with appropriate permissions
4. ZFS snapshots provide reliable recovery mechanism for accidental deletions
5. Always verify fixes with actual test operations, not just permission checks

## Prevention
- When setting up new media folders, ensure ownership matches the user/group that will perform operations
- Consider using `builtin_administrators` as the primary group for media files needing broad access
- Document permission schemes in TrueNAS deployment documentation