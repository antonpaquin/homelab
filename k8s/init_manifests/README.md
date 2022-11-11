Anton: have not yet figured out if this actually gets applied when copied to /etc/kubernetes/manifests
NB calico.yaml is not *exactly* the default version, had to change  
            - name: CALICO_IPV4POOL_CIDR
              value: "10.244.0.0/18"
To make subnetting work (hopefully it works?)
