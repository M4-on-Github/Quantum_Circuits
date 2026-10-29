# Submission approvals

Only the user writes here. No agent's write guard allows this folder.

To approve proposal `knowledge/submissions/S-NNN.md`, create `approvals/S-NNN.txt` containing the SHA-256 of the exact file to submit (stated in the proposal):

```powershell
(Get-FileHash submissions\S-NNN.zip -Algorithm SHA256).Hash.ToLower() | Out-File -Encoding ascii approvals\S-NNN.txt
```

The submit hook refuses any submission whose file hash isn't in the matching approval file.
