# Installation steps
- Install Nvidia driver (headless/server version)
- Install nvidia-container-toolkit
    ```sh
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
    && \
        sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
    ```
- Reboot (or at least load the Nvidia driver and restart K3s)
- Create runtimeClass "nvidia"
    ```sh
    kubectl apply -f nvidia.runtime-class.yaml
    ```
- Install nvidia-device-plugin (and enable CUDA time slicing)
    ```sh
    helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
    helm repo update
    helm install nvdp nvdp/nvidia-device-plugin \
        --namespace nvidia-device-plugin --create-namespace \
        --version 0.14.5 -f nvidia-device-plugin.values.yaml
    ```

# Sources
- K3s instructions for NVIDIA setup... (https://docs.k3s.io/advanced#nvidia-container-runtime-support)

# Gotchas
- nvidia-container-runtime has to be set either as default or it needs to be present on every pod that wants to use the GPU (in `runtimeClassName`)

# Still ToDo / ToVerify
- Do we really need the fabricmanager, the K3s documentation mentions? Probably not...
- Is setting the nvidia container runtime as default the only option for avoiding `runtimeClassName: nvidia` on every pod? (is that even an issue?)

