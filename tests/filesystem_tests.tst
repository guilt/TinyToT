# File System Test Cases
# Format: PROMPT | EXPECTED_CATEGORY | EXPECTED_TOOL | EXPECTED_PATTERNS

How many PNG files are in my home directory? | fs | filesystem | Category: fs.*Directory Traversal.*recursive search
Find all text files in the current directory | fs | filesystem | Category: fs.*Directory Traversal.*permissions
How do I organize my file system hierarchy? | fs | none | Category: fs.*Directory Traversal.*directory tree
What's the best way to backup important files? | fs | none | Category: fs.*File Backup Strategy.*incremental.*full backup
How do I find duplicate files on my system? | fs | filesystem | Category: fs.*Directory Traversal.*collect paths
Explain the difference between absolute and relative paths | fs | none | Category: fs.*Directory Traversal.*starting from root
How do I set up file permissions correctly? | fs | none | Category: fs.*Permission Management.*chmod
What's the fastest way to search for files by content? | fs | filesystem | Category: fs.*Directory Traversal.*recursive search
How do I monitor disk space usage? | fs | filesystem | Category: fs.*Disk Space Analysis.*du command
Explain file system fragmentation and defragmentation | fs | none | Category: fs.*Directory Traversal.*directory tree
