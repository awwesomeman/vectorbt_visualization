# vectorbt_visualization
This project aims to visualize vectorized back testing results with interactive plot and other detailed information..

# Demo code

``` python
# ma strategy
trade = My_Strategy()
trade.get_stock('2303',start='2021-01-01',end='2021-07-15',freq='30T')
trade.MA()
df = trade.run()
trade.plot()

```
![image](https://user-images.githubusercontent.com/40668464/139542755-6b0d8022-e2a0-4314-89fb-eb1c5fa79a62.png)

![image](https://user-images.githubusercontent.com/40668464/139542711-ca77cb53-9696-4fdd-a2d5-27cf6f4c6a6d.png)
