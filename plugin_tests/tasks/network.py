from autopilot.tasks import Task
from autopilot.data.models.protocol import Trial_Data
from autopilot.networking import Net_Node
from autopilot import prefs
from pydantic import Field
from datetime import datetime
from threading import Event
from asyncio import Queue
from typing import Optional

class Network_Latency(Task):

    PARAMS = {}
    PARAMS['n_messages'] = {
        'tag': 'Number of messages to send back and forth',
        'type': 'int'
    }

    class TrialData(Trial_Data):
        send_time: datetime = Field(..., description="Timestamp of sending the initial message")
        recv_time: datetime = Field(..., description="Timestamp of when the message was received by the second pi")

    LEADER_PORT = 5580
    FOLLOWER_PORT = 5581

    def __init__(self, n_messages:int=None, role:str="leader", leader_ip:str=None, **kwargs):
        super(Network_Latency, self).__init__(**kwargs)

        self.n_messages = int(n_messages)
        self.role = role
        self.node = None # type: Optional[Net_Node]
        self.leader_ip = leader_ip
        self.ready_event = Event()
        self.ready_event.clear()
        self.quitting = Event()
        self.quitting.clear()
        self.response_q = Queue()

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
        return Net_Node(
            id=f"{self.role}",
            upstream=self.upstream,
            port=self.upstream_port,
            upstream_ip=self.upstream_ip,
            router_port=self.router_port,
            listens=self.listens
        )

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
        self.node.send(to="leader", key="RESPONSE", value={'recv_time': received, 'message_number':msg['message_number']})


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

    def volley(self):

        if self.role == "leader":
            self.ready_event.wait()
        else:
            # follower just waits, all of its actions happen in callbacks
            self.quitting.wait()
            return {}

        for i in range(self.n_messages):

            send_time = datetime.now().isoformat()
            self.node.send(to="follower", key="CALL", value={'message_number': i})

            response = await self.response_q.get()
            if response['message_number'] != i:
                self.logger.warning(f"Received response out of order? i:{i}, response:{response['message_number']}")

            yield {
                'send_time':send_time,
                'recv_time':response['recv_time'],
                'trial_n':i,
                'TRIAL_END':True
            }

            if self.quitting.is_set():
                break

        self.node.send(to='follower', key="STOP", value={})
