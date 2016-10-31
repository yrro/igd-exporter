import concurrent.futures
import socket
import wsgiref.simple_server

def server_class(bind_address, bind_v6only, max_threads):
    '''
    Give us a class that can both listen on an IPv6 socket and use a thread
    pool to serve multiple requests simultaneously.
    '''
    class ThreadPoolServer():
        ex = concurrent.futures.ThreadPoolExecutor(max_threads)

        def process_request(self, request, client_address):
            ThreadPoolServer.ex.submit(self.__process_request_thread, request, client_address)

        def __process_request_thread(self, request, client_address):
            try:
                self.finish_request(request, client_address)
                self.shutdown_request(request)
            except:
                self.handle_error(request, client_address)
                self.shutdown_request(request)

        def server_close(self):
            ThreadPoolServer.ex.shutdown()
            super().close()

    class IPv64Server():
        address_family = socket.AF_INET6 if bind_address.version == 6 else socket.AF_INET

        def server_bind(self):
            self.socket.setsockopt(socket.IPPROTO_IP, 15, 1) # IP_FREEBIND
            if bind_v6only is not None and bind_address.version == 6:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, bind_v6only)
            super().server_bind()

    class Server(ThreadPoolServer, IPv64Server, wsgiref.simple_server.WSGIServer):
        pass

    return Server
