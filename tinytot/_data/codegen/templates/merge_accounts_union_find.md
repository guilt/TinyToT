# Merge Accounts Union Find

<\!-- Merge Accounts (Union Find) Question Merge user accounts using the union-find data structure. -->

## python
```python
class Solution:
    def accountsMerge(self, accounts):
        """
        Merge user accounts.
        """

        from collections import defaultdict
        parent = {}
        emailToName = {}

        def find(email):
            if parent[email] != email:
                parent[email] = find(parent[email])
            return parent[email]

        # Build parent and email->name mapping
        for account in accounts:
            name = account[0]
            for email in account[1:]:
                if email not in parent:
                    parent[email] = email
                emailToName[email] = name
                parent[find(account[1])] = find(email)

        unions = defaultdict(list)
        for email in parent:
            root = find(email)
            unions[root].append(email)

        mergedAccounts = []
        for rootEmail, emailList in unions.items():
            mergedAccounts.append([emailToName[rootEmail]] + sorted(emailList))
        return mergedAccounts
```
