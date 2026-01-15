from fakts.models import IonscaleLayer
from .repo import django_repo

def sync(layer: IonscaleLayer) -> IonscaleLayer:
    
    # Create iam policy for all organization members
    members = layer.organization.memberships.all()
    
    # Build policy
    policy = {
        "subs": [str(m.user.pk) for m in members]
    }
    
    django_repo.update_policy(layer.tailnet_name, policy)
    
    
    

    return layer