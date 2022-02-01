# urequests_ff -- Fire and Forget  
## urequests with asyncio and ssl  
## Example(as urequests):  
```python
import uasyncio as asyncio  
import urequests_ff as urequests  

async def create_task():  
	asyncio.create_task(asend())   


async def asend():  
	res = await urequest.post(url,data,headers)  
	res.close()  
    
asyncio.run(create_task())
```
