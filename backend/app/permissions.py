"""Server membership roles map to actions; every permission defaults to denied."""
ROLE_ACTIONS={
 'commuter': frozenset({'profile.read','ride.read','wallet.read'}),
 'campaign_manager': frozenset({'profile.read','campaign.manage'}),
 'sponsor_admin': frozenset({'profile.read','sponsor_campaign.manage'}),
 'support_agent': frozenset({'profile.read','support.metadata'}),
 'fraud_reviewer': frozenset({'profile.read','fraud.review','audit.read'}),
 'analyst': frozenset({'profile.read','analytics.aggregate'}),
 'super_admin': frozenset({'profile.read','ride.read','wallet.read','campaign.manage','sponsor_campaign.manage',
                         'support.metadata','fraud.review','audit.read','analytics.aggregate','memberships.manage'}),
}


def allowed_actions(roles):
    return frozenset().union(*(ROLE_ACTIONS.get(role,frozenset()) for role in roles))


def permits(roles,action):
    return action in allowed_actions(roles)
