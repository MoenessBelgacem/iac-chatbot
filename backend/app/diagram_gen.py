"""
Générateur de diagrammes d'architecture Mermaid.

Produit un diagramme Mermaid.js à partir d'une DemandeRessource,
permettant une visualisation instantanée de l'infrastructure générée.
"""


def generer_diagramme(demande: dict, nom_ressource: str) -> str:
    """
    Génère un diagramme Mermaid représentant l'architecture de la ressource.

    Args:
        demande: dict issu de DemandeRessource.model_dump()
        nom_ressource: nom de la ressource générée

    Returns:
        str: code Mermaid du diagramme
    """
    resource_type = demande["resource_type"]
    platform = demande["platform"]

    if resource_type == "vm" and platform == "vsphere":
        return _diagramme_vsphere_vm(demande, nom_ressource)
    elif resource_type == "container" and platform == "openshift":
        return _diagramme_openshift_container(demande, nom_ressource)
    elif resource_type == "vm" and platform == "openshift":
        return _diagramme_kubevirt_vm(demande, nom_ressource)
    else:
        return ""


def _diagramme_vsphere_vm(demande: dict, nom: str) -> str:
    """Diagramme pour une VM vSphere."""
    return f"""graph TD
    VSPHERE["🏢 VMware vSphere"]
    DC["📁 Datacenter"]
    CLUSTER["⚙️ Cluster"]
    RP["📦 Resource Pool"]
    DS["💾 Datastore"]
    NET["🌐 Network<br/>{demande.get('network', 'default')}"]
    VM["{nom}<br/>💻 VM"]
    CPU["🔲 {demande['cpu']} vCPU"]
    RAM["🧠 {demande['ram_gb']} Go RAM"]
    DISK["💿 {demande['storage_gb']} Go"]
    IMG["📀 {demande['image']}"]

    VSPHERE --> DC
    DC --> CLUSTER
    CLUSTER --> RP
    DC --> DS
    DC --> NET
    RP --> VM
    VM --> CPU
    VM --> RAM
    VM --> DISK
    DS -.-> DISK
    NET -.-> VM
    IMG -.-> VM

    style VM fill:#4CAF50,stroke:#2E7D32,color:#fff
    style VSPHERE fill:#1565C0,stroke:#0D47A1,color:#fff
    style DC fill:#42A5F5,stroke:#1E88E5,color:#fff"""


def _diagramme_openshift_container(demande: dict, nom: str) -> str:
    """Diagramme pour un conteneur OpenShift."""
    return f"""graph TD
    OCP["☸️ OpenShift"]
    NS["📂 Namespace<br/>chatbot-iac"]
    DEP["🔄 Deployment<br/>{nom}"]
    POD["🐳 Pod"]
    CTR["📦 Container<br/>{demande['image']}"]
    SVC["🌐 Service<br/>ClusterIP"]
    PVC["💾 PVC<br/>{demande['storage_gb']} Go"]
    CPU["🔲 {demande['cpu']} vCPU"]
    RAM["🧠 {demande['ram_gb']} Go RAM"]

    OCP --> NS
    NS --> DEP
    NS --> SVC
    NS --> PVC
    DEP --> POD
    POD --> CTR
    CTR --> CPU
    CTR --> RAM
    SVC -.->|port| POD
    PVC -.->|mount| CTR

    style CTR fill:#FF9800,stroke:#E65100,color:#fff
    style OCP fill:#E53935,stroke:#B71C1C,color:#fff
    style SVC fill:#26A69A,stroke:#00796B,color:#fff
    style PVC fill:#7E57C2,stroke:#4527A0,color:#fff"""


def _diagramme_kubevirt_vm(demande: dict, nom: str) -> str:
    """Diagramme pour une VM KubeVirt sur OpenShift."""
    return f"""graph TD
    OCP["☸️ OpenShift"]
    NS["📂 Namespace<br/>chatbot-iac"]
    VMR["🖥️ VirtualMachine<br/>{nom}"]
    SPEC["⚙️ Domain Spec"]
    ROOTDISK["💿 Root Disk<br/>{demande['image']}"]
    CLOUDINIT["☁️ Cloud-Init"]
    PVC["💾 PVC<br/>{demande['storage_gb']} Go"]
    NET["🌐 Network<br/>{demande.get('network', 'default')}<br/>masquerade"]
    CPU["🔲 {demande['cpu']} Cores"]
    RAM["🧠 {demande['ram_gb']} Go RAM"]

    OCP --> NS
    NS --> VMR
    NS --> PVC
    VMR --> SPEC
    SPEC --> CPU
    SPEC --> RAM
    SPEC --> ROOTDISK
    SPEC --> CLOUDINIT
    SPEC --> NET
    PVC -.-> ROOTDISK

    style VMR fill:#4CAF50,stroke:#2E7D32,color:#fff
    style OCP fill:#E53935,stroke:#B71C1C,color:#fff
    style PVC fill:#7E57C2,stroke:#4527A0,color:#fff
    style NET fill:#26A69A,stroke:#00796B,color:#fff"""
