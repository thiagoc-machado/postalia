from rest_framework.response import Response


def api_ok(data=None, status=200):
    return Response(data or {}, status=status)
