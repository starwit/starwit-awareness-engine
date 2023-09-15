# How-To
- Generally, follow the K3s instructions...

# Gotchas
- nvidia-container-runtime has to be set either as default or it needs to be present on every pod that wants to use the GPU (in `runtimeClassName`)

# Still ToDo / ToVerify
- Do we really need the fabricmanager, the K3s documentation mentions? Probably not...
- Is setting the nvidia container runtime as default the only option for avoiding `runtimeClassName: nvidia` on every pod? (is that even an issue?)