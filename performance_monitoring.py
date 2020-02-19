#vcpu and  vmem of all vm's
#print all vms in ascending order based on cpu and memory usage
import libvirt
import sys
import time

#take CPU_T and MEM_T as threshhold values
CPU_T=input("Enter CPU Threshold in %: ")
MEM_T=input("Enter Memory Threshold in %: ")
mov_win=input("Enter Moving window size in seconds:")
poll_interval=input("Enter polling interval in seconds:")
#constraints polling window and moving window should be atleast 1 sec

conn=libvirt.open('qemu:///system')
if conn == None:
    print('Failed to open connection to qemu:///system')
    exit(1)

#get the VM ID's
def get_VM_IDs(conn):
        domainIDs=conn.listDomainsID()
        if domainIDs == None:
           print("Failed to get list of VMs")
        return domainIDs

#get CPU time on a VM
def get_CPU_time(ID):
        dom = conn.lookupByID(ID)
        stats = dom.getCPUStats(True)
        return stats[0]['cpu_time']

#get avg Memory stats on a VM
def get_MEM_stats(ID):
        dom=conn.lookupByID(ID)
        stats  = dom.memoryStats()
        mem_util=(stats["rss"]/float(stats["actual"]))*100
        return mem_util
#mem_util=(rss/actual)*100

#get avg CPU stats on a VM
def get_CPU_stats(CPU_T2,CPU_T1):
        CPU_Avg=(CPU_T2-CPU_T1)*(10**(-9))*100
        return CPU_Avg
#cpu_avg=(CPU time change/Actual time)*100

#get VM name from ID
def get_VM_Name(ID):
        domain = conn.lookupByID(ID)
        return domain.name()

#get timestamp
def get_timestamp():
    ts=time.time()
    readable=time.ctime(ts)
    return readable

#monitoring script for every 1 second interval
count=0

IDs = get_VM_IDs(conn)
dict_Mem_Avg={}
dict_CPU_Avg={}
dict_CPU={}
dict_MEM={}
for ID in IDs:
  dict_Mem_Avg[ID]=[]
  dict_CPU_Avg[ID]=[] 

 
while(1):
   IDs = get_VM_IDs(conn) #gives list of all VM's
   dict_CPUtime={}

   for ID in IDs:
      dict_CPUtime[ID]=get_CPU_time(ID)
 
   time.sleep(1) #sleep for 1 sec
   count+=1
 
   for ID in IDs:
      CPU_T2=get_CPU_time(ID)
      CPU_T1=dict_CPUtime[ID]

      Mem_Avg=get_MEM_stats(ID) #get mem and cpu averages
      CPU_Avg=get_CPU_stats(CPU_T2,CPU_T1)
 
     #store CPU and mem avg in list
      mov_window_mem=dict_Mem_Avg[ID]
      if len(mov_window_mem) >= mov_win:
         mov_window_mem.pop(0)
      mov_window_mem.append(Mem_Avg)
      dict_Mem_Avg[ID]=mov_window_mem
 
      mov_window_cpu=dict_CPU_Avg[ID]
      if len(mov_window_cpu) >= mov_win:
          mov_window_cpu.pop(0)
      mov_window_cpu.append(CPU_Avg)
      dict_CPU_Avg[ID]=mov_window_cpu

      dict_MEM[ID]=sum(mov_window_mem)/float(len(mov_window_mem)) # store the averages in a dictionary
      dict_CPU[ID]=sum(mov_window_cpu)/float(len(mov_window_cpu))
  
   if count>=poll_interval:
    count=0
    sorted_CPU_Avg= sorted(dict_CPU.items(),key=lambda x:x[1]) # sort the dictionary
    sorted_MEM_Avg= sorted(dict_MEM.items(),key=lambda x:x[1])
    print(get_timestamp())
    print("CPU Usage")
    for i in sorted_CPU_Avg:
       print(get_VM_Name(i[0])+": "+str(round(i[1],2))+"%")
    print("MEM Usage")
    for i in sorted_MEM_Avg:
       print(get_VM_Name(i[0])+": "+str(round(i[1],2))+"%")
    fp=open("Alerts_log.txt","a")
    for i in sorted_CPU_Avg:
        sorted_CPU_Avg_i=round(i[1],2)
        if (sorted_CPU_Avg_i > CPU_T):
          string=("Alert "+ get_VM_Name(i[0])+"  CPU Usage:"+str(sorted_CPU_Avg_i)+"%   "+get_timestamp())
          fp.write(string)
          fp.write("\n")
          print(string)
         # print("Alert "+ str(i[0])+" CPU Usage:"+str(sorted_CPU_Avg_i)+"%  "+get_timestamp())
    for i in sorted_MEM_Avg:
       sorted_MEM_Avg_i=round(i[1],2)
       if (sorted_MEM_Avg_i > MEM_T):
          string=("Alert "+ get_VM_Name(i[0])+"  MEM Usage:"+str(round(i[1],2))+"%   "+get_timestamp())
          fp.write(string)
          fp.write("\n")
          print(string)
    fp.close()
    print(" ")
    print(" ")
 
conn.close()
