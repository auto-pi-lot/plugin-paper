from autopilot.tasks import Task
from autopilot.data.models.protocol import Trial_Data
from autopilot.networking import Net_Node
from autopilot import prefs
from pydantic import Field
from datetime import datetime
from threading import Event
from queue import Queue
from typing import Optional
from time import sleep

class Network_Latency(Task):

    PARAMS = {}
    PARAMS['n_messages'] = {
        'tag': 'Number of messages to send back and forth',
        'type': 'int'
    }
    PARAMS['follower_id'] = {
        'tag': 'ID of the pilot that will be used as the follower, needed to route the start message to it',
        'type': 'str'
    }
    PARAMS['iti'] = {
        'tag': 'inter-trial interval, in ms',
        'type': 'float'
    }

    PLOT = {
        'data': {
            'latency': 'line'
        },
        'x_width': 1000,
        'y_range': [0,3]
    }

    class TrialData(Trial_Data):
        send_time: datetime = Field(..., description="Timestamp of sending the initial message")
        recv_time: datetime = Field(..., description="Timestamp of when the message was received by the second pi")
        latency: float = Field(..., description="Difference between receive and send time, in ms")

    LEADER_PORT = 5580
    FOLLOWER_PORT = 5581

    def __init__(self, n_messages:int=None, iti:float=5, role:str="leader", leader_ip:str=None, follower_id:str=None, **kwargs):
        super(Network_Latency, self).__init__(**kwargs)

        self.n_messages = int(n_messages)
        self.role = role
        self.node = None # type: Optional[Net_Node]
        self.follower_id = follower_id
        self.leader_ip = leader_ip
        self.ready_event = Event()
        self.ready_event.clear()
        self.quitting = Event()
        self.quitting.clear()
        self.response_q = Queue()
        self.iti = iti
        self.start_kwargs = kwargs

        self.listens = {
            'READY': self.l_ready,
            'STOP': self.l_stop,
            'CALL': self.l_call,
            'RESPONSE': self.l_response
        }

        if self.role == 'leader':
            self.init_leader()
        else:
            self.init_follower()

        self.stages = iter([self.volley])


    def init_leader(self):
        """
        Initialize leader and send a message to the follower that it should contact us!
        """
        self.upstream = 'T'
        self.upstream_port = prefs.get('PUSHPORT')
        self.upstream_ip = prefs.get('TERMINALIP')
        self.router_port = self.LEADER_PORT



        self.node = self.init_networking()
        # make initial connection to terminal
        self.node.send(to='T', key="INIT", value={})

        start_msg = self.start_kwargs.copy()
        del start_msg['stage_block']
        start_msg['role'] = 'follower'
        start_msg['leader_ip'] = self.node.ip
        start_msg['n_messages'] = self.n_messages

        # send multihop message to start the follower!
        to = ['T', self.follower_id]
        self.logger.debug(f"sending message to: {to}")
        self.node.send(to=to,
                       key="START",
                       value=start_msg)


    def init_follower(self):
        """
        After receiving a message from the leaer
        :param leader_msg:
        :type leader_msg:
        :return:
        :rtype:
        """
        self.upstream_port = self.LEADER_PORT
        self.upstream = 'leader'
        self.router_port = None
        self.upstream_ip = self.leader_ip

        self.node = self.init_networking()

        self.node.send(to='leader', key="READY", value={})

    def init_networking(self,) -> Net_Node:
        node = Net_Node(
            id=f"{self.role}",
            instance=False,
            upstream=self.upstream,
            port=self.upstream_port,
            upstream_ip=self.upstream_ip,
            router_port=self.router_port,
            listens=self.listens
        )
        return node


    def l_ready(self, msg):
        """
        The follower is signaling to the leader (us) that it's ready
        """
        self.ready_event.set()

    def l_call(self, msg):
        """
        Receive a message from the leader with some message number, and then respond
        with the time that we received it.
        """
        received = datetime.now().isoformat()
        self.node.send(
            to="leader", 
            key="RESPONSE", 
            value={
            'recv_time': received, 
            'message_number':msg['message_number']
            }, 
            flags={'NOREPEAT':True})


    def l_response(self, msg):
        """
        Receive a message from the follower with the timestamp that it received the
        call
        """
        self.response_q.put(msg)

    def l_stop(self, msg):
        """
        Receive a message from the leader telling us to stop
        """
        self.quitting.set()
        self.ready_event.set()

    def _volley(self, i:int, subject:str):

        send_time = datetime.now()
        self.node.send(
            to="follower", 
            key="CALL", 
            value={'message_number': i}, 
            flags={'NOREPEAT':True})

        response = self.response_q.get()
        if response['message_number'] != i:
            self.logger.warning(f"Received response out of order? i:{i}, response:{response['message_number']}")

        # get difference
        recv_time = datetime.fromisoformat(response['recv_time'])
        latency = (recv_time - send_time).total_seconds() * 1000


        self.node.send(to='T', key='DATA', value={
            'send_time': send_time.isoformat(),
            'recv_time': recv_time.isoformat(),
            'latency': latency,
            'pilot': prefs.get('NAME'),
            'trial_num': i,
            'subject': subject,
            'TRIAL_END': True,
        })

    def volley(self):

        subject = prefs.get('SUBJECT')

        if self.role == "leader":
            self.ready_event.wait()
        else:
            # follower just waits and then returns, all of its actions happen in callbacks
            self.quitting.wait()
            return {}

        for i in range(self.n_messages):

            self._volley(i, subject)
            time.sleep(self.iti/1000)

            if self.quitting.is_set():
                break

        self.node.send(to='follower', key="STOP", value={})

    def end(self):
        self.node.release()
        self.quitting.set()
        super(Network_Latency, self).end()

