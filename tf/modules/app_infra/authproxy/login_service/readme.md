To be used in namespaces other than the one where the main authproxy service is located

I have a theory this should work but it currently doesn't

Basically, the limiting factor in having authproxies in many namespaces is the /_authproxy ingress rule needs a local target, and we need that rule for set-cookie
Currently I'm getting 504 timeout's for some reason?
What's timing out? Is it authproxy? are my requests going to some bizarro port?

Should be:
    rook ceph-dashboard ingress /_authproxy
    --> rook authproxy service (externalName authproxy.default.svc.cluster.local, p 80)
    --> default authproxy service (p 80 -> p 4000)
    --> default authproxy pod

I get a URL in my browser when I try to use ceph-dashboard.antonpaqu.in
    https://ceph-dashboard.antonpaqu.in/_authproxy/login_success?AuthProxyToken=gAAAAABjYE0Xu3pFK1zgN5LFHohD_qwAlfQlP_EpjUoA9ppL21yF6jOcyaVE5iFKdgJao19DLw5BdN8XGPZ6OebF32qbwo1-Qtbl8vgiu2BQbu6LbzU01sZnSq8q9t553XbazzJqVtkruIK-dBUNTw_QKgdqFCczBNLdhYkoAn5OkdW5yGj8XsZM2NUSksPqP90K2L-b6uyjZCNuaFgWrWZyhsDg_tKfeg%3D%3D&rd=https%3A%2F%2Fceph-dashboard.antonpaqu.in%2F

so that's the _authproxy/login_success endpoint
but I notice the host in the authproxy logs for that request is authproxy.default.svc.cluster.local
... does that get used internally somewhere? I don't think we're doing host routing except at the ingress level so cluster-local endpoints should be fine