Scripts and notebooks for [CycloRank](https://mlumiste.com//projects/cyclorank/) project.
All credits to [Mihkel Lumiste](https://mlumiste.com/) [github](https://github.com/skandium) for the original code.

Current update aims to provide this cycling infrastructure ranking tool for Czechia for all cities above 10000 inhabitants and 
for every year.

Maintained by [AutoMAT](https://automat.cz/), [Městem na kole](https://mestemnakole.cz) 
and [Daniel Soutner](https://daniel.soutner.cz/).  

![](doc/Plzeň_infra.png)

## Installation

```shell
sudo apt install osmium-tool
# or for mac
brew install osmium-tool

pip install -r requirements.txt
```

## Run

First downloading and processing script (about 8hrs):
```shell
./_run_cyklorank_v2.sh
```
And then run the notebook to generate the table and plots.
