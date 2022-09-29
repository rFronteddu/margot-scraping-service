import logging
from concurrent import futures
from threading import Thread
import grpc
import api_pb2
import api_pb2_grpc
import camera


def delegate(*args):
    t = Thread(target=args[0].run())
    t.start()
    t.join()


class Api(api_pb2_grpc.ScraperServicer):
    def Scrape(self, request, context):
        print(request)

        # send a list of urls containing videos to scrape links
        # for each found url create a response object
        scraped_videos = []
        for url in request.urls:
            threaded_camera = camera.ThreadedCameraStream(url)
            t = Thread(target=delegate, args=[threaded_camera])
            t.start()
            scraped_videos.append(
                api_pb2.ScrapeResponse.ScrapedUrl(
                    base_url=url,
                    rtsp_url=threaded_camera.rtsp_url,
                )
            )
        return api_pb2.ScrapeResponse(
            scraped_urls=scraped_videos
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
