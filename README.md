# urequests_ff -- Fire and Forget  
## urequests with asyncio and ssl  
## Example(as urequests):  
```python
import uasyncio as asyncio  
import urequests_ff as urequests  

async def create_task():  
	asyncio.create_task(asend())   


async def asend():  
	res = await urequests.post(url,data,headers)  
	res.close()  
    
asyncio.run(create_task())
```

## references:
1: https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md  
2: https://forum.micropython.org/viewtopic.php?f=18&t=11895  
