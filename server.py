import logging
from concurrent import futures
import grpc
import api_pb2
import api_pb2_grpc


class Api(api_pb2_grpc.ScraperServicer):
    def Scrape(self, request, context):
        print(request)
        return api_pb2.ScrapeResponse(
            scraped_urls=[
                api_pb2.ScrapeResponse.ScrapedUrl(
                    base_url='https://example.com',
                    rtsp_url='rtsp://example.com',
                )
            ]
        )


def serve():
    try:
        port = '50051'
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        api_pb2_grpc.add_ScraperServicer_to_server(Api(), server)
        server.add_insecure_port('[::]:' + port)
        server.start()
        print("Server started, listening on " + port)
        server.wait_for_termination()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    logging.basicConfig()
    serve()
