<<<<<<< HEAD
=======
import os
import cloudinary.uploader
>>>>>>> nimra-fix-develop
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

<<<<<<< HEAD
import cloudinary.uploader

from accounts.serializers.upload_serializer import FileUploadSerializer


class FileUploadView(APIView):
=======
MAX_FILE_SIZE_MB = 5
ALLOWED_EXTENSIONS = {".pdf"}

class FileUploadView(APIView):
    """
    POST /api/upload/ — Sirf Teacher aur Student file upload kar sakte hain.
    Teacher assignment attach karega, Student apna submission upload karega.
    Admin/Parent ko access deny hoga.
    """

>>>>>>> nimra-fix-develop
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
<<<<<<< HEAD
        operation_summary="Upload a file (multipart/form-data)",
=======
        operation_summary="Upload a PDF file (max 5 MB)",
>>>>>>> nimra-fix-develop
        consumes=["multipart/form-data"],
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
<<<<<<< HEAD
                description="File to upload",
=======
                description="PDF file to upload (max 5 MB)",
>>>>>>> nimra-fix-develop
            )
        ],
        responses={
            201: openapi.Response(
                description="Upload successful",
                examples={"application/json": {"url": "https://..."}},
            ),
            400: "Bad request",
<<<<<<< HEAD
        },
    )
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data["file"]
        result = cloudinary.uploader.upload(file_obj, resource_type="auto")
        return Response({"url": result["secure_url"]}, status=status.HTTP_201_CREATED)

=======
            403: "Forbidden",
            502: "Cloud upload failed",
        },
    )
    def post(self, request):
        # ✅ Role check (safe: role missing ho to crash na ho)
        role = getattr(request.user, "role", None)
        role_name = getattr(role, "role_name", None)
        if role_name not in ["Student", "Teacher"]:
            return Response(
                {"detail": "Only students and teachers can upload files."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ✅ File input check
        if not request.FILES:
            return Response(
                {"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"detail": "No file provided. Expected form-data key: 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ File size check
        if file_obj.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return Response(
                {
                    "detail": (
                        f"File too large. Max allowed size is {MAX_FILE_SIZE_MB} MB."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ File type check (extension based)
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Response(
                {
                    "detail": (
                        f"File type '{ext}' not allowed. Only PDF files are accepted."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Upload to Cloudinary (defensive: Cloud errors ko 500 na banne do)
        try:
            result = cloudinary.uploader.upload(file_obj, resource_type="auto")
        except Exception as e:
            return Response(
                {
                    "detail": "File upload failed. Please try again later.",
                    "error": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        secure_url = result.get("secure_url") if isinstance(result, dict) else None
        if not secure_url:
            return Response(
                {"detail": "Upload succeeded but Cloudinary returned no URL."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"url": secure_url}, status=status.HTTP_201_CREATED)
>>>>>>> nimra-fix-develop

