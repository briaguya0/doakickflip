# How do we detect that THUG Pro changed the archive since our install?

Type: grilling
Status: open

## Question

When a THUG Pro update replaces thugpro_qb.prx, our backup of the original is stale. How does the app notice the live archive isn't the one it installed (e.g. a hash of what we wrote, or matching THUG Pro's manifest CRCs), and treat it as the new original?
