G_ENDPOINT = 'http://devapi.globelabs.com.ph'
G_VERSION  = 'v1'
SMS_MSG    = "test msg"

# end fuckin points
G_DIALOG            = 'http://developer.globelabs.com.ph/dialog/oauth?app_id={}'
G_AUTH_ENDPOINT     = 'http://developer.globelabs.com.ph/oauth/access_token'

G_CHARGING_ENDPOINT = '{}/payment/{}/transactions/amount'.format(G_ENDPOINT, G_VERSION)
G_SMS_ENDPOINT = '{}/smsmessaging/{}/outbound/'.format(G_ENDPOINT, G_VERSION) + '{}/requests'
