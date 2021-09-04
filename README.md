# MaxPowerFlow

### About

Python script for calculating maximum transmission power flow in branch group of power grid according with [Russian PSO criterias](https://www.so-ups.ru/fileadmin/files/laws/standards/st_max_power_rules_004-2020.pdf) (rus).

* Solution is based on calculation engine Astra from the [RastrWin3](https://www.rastrwin.ru/) library collection.

### Requirments

* Python (x32) 2.7 (or upper)
* Pywin32 installed in python enviroment
* Installed RastrWin3 with registered COM AstraLib 1.0

Model of powergrid should be described in RastrWin3 regime files

### Usage

#### Specify parameters in cmd:

```sh
MaxPowerFlow [-KEY1] <ARG1> [-KEY2] <ARG2> ...
```
#### Necessary parameters:
| Param | Description |
| ------ | ------ |
| -rg2 | Path to RastrWin3 regime file. |
| -rg2template | Path to RastrWin3 rg2 template file. |
| -bg | Path to json file, which contains list of branches in branch group |
| -outages | Path to json file, which contains list of branches for calculating emergency PF |
| -pfvv | Path to csv file, which contains list of nodes and dP params in power flow variance vector |


### Example usage
```sh
MaxPowerFlow -rg2 "Tests\assets\regime.rg2" -pfvv "Tests\assets\vector.csv" -rg2template "src\assets\rastr_templates\режим.rg2" -bg "Tests\assets\flowgate.json" -outages "Tests\assets\faults.json" 
```
#### Output:
```sh
• 20% Pmax запас в нормальном режиме:     2216.57
• 15% Ucr запас в нормальном режиме:      2706.5
• ДДТН в нормальном режиме:               1708.17
• 8% Pmax запас в послеаварийном режиме:  2132.61
• 10% Ucr запас в послеаварийном режиме:  2295.08
• АДТН в послеаварийном режиме:	          1479.26
```
