""" Module for API testing. """

async def test_health(cli):
    resp = await cli.get('/api/health')
    assert resp.status == 200
    

