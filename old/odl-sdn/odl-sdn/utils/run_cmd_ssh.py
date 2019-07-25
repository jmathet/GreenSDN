#!/usr/bin/python

import os
import sys
import select
import paramiko
import time


class Commands:
    def __init__(self, retry_time=0):
        self.retry_time = retry_time
        pass

    def run_cmd(self, host_ip, user, pswd, cmd):
        i = 0
        while True:
        # print("Trying to connect to %s (%i/%i)" % (self.host, i, self.retry_time))
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host_ip, username=user, password=pswd)
                break
            except paramiko.AuthenticationException:
                print("Authentication failed when connecting to %s" % host_ip)
                sys.exit(1)
            except Exception as e:
                print(e)
                print("Could not SSH to %s, waiting for it to start" % host_ip)
                i += 1
                time.sleep(2)

        # If we could not connect within time limit
            if i >= self.retry_time:
                print("Could not connect to %s. Giving up" % host_ip)
                sys.exit(1)
        # After connection is successful
        # Send the command
        # print command
        print "> " + cmd
        # execute commands
        stdin, stdout, stderr = ssh.exec_command(cmd)
        # TODO() : if an error is thrown, stop further rules and revert back changes
        # Wait for the command to terminate
        output=''
        while not stdout.channel.exit_status_ready():
        # Only print data if there is data to read in the channel
            if stdout.channel.recv_ready():
                rl, wl, xl = select.select([ stdout.channel ], [ ], [ ], 0.0)
                if len(rl) > 0:
                    tmp = stdout.channel.recv(1024)
                    output = output + tmp.decode()        
          
        # Close SSH connection
        ssh.close()
        return output

def main(args=None):
    if args is None:
        print "arguments expected"
    else:
        # args = {'<ip_address>', <list_of_commands>}
        mytest = Commands()
        print mytest.run_cmd(host_ip=args[0], user=args[1], pswd=args[2], cmd=args[3])
    return


if __name__ == "__main__":
    main(sys.argv[1:])