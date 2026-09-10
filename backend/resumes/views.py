from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.services import get_active_profile
from .models import Resume
from .serializers import ResumeSerializer
from rest_framework.parsers import MultiPartParser
from ai.service import AIServiceError, extract_resume


class ResumeDetailView(APIView):
    def get_object(self, request):
        profile = get_active_profile(request)
        resume, _ = Resume.objects.get_or_create(
            profile=profile,
            defaults={'full_name': '', 'email': ''},
        )
        return resume

    def get(self, request):
        resume = self.get_object(request)
        return Response(ResumeSerializer(resume).data)

    def patch(self, request):
        resume = self.get_object(request)
        serializer = ResumeSerializer(resume, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ResumeImportView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if uploaded_file is None:
            return Response({'detail': 'No file uploaded'}, status=400)

        raw_text = self._extract_text(uploaded_file)
        if not raw_text.strip():
            return Response(
                {'detail': 'Could not read any text from that file. Try a different file or fill the form manually.'},
                status=400,
            )

        active_profile = get_active_profile(request)
        try:
            draft = extract_resume(active_profile, raw_text)
        except AIServiceError as exc:
            return Response({'detail': str(exc)}, status=502)

        # Deliberately NOT saved here — this is a draft for the frontend
        # to pre-fill the editor with. Nothing is written to Resume
        # until the user reviews and hits Save (ADR-007).
        return Response(draft)

    def _extract_text(self, uploaded_file):
        name = uploaded_file.name.lower()
        if name.endswith('.docx'):
            import docx
            document = docx.Document(uploaded_file)
            return '\n'.join(p.text for p in document.paragraphs)
        elif name.endswith('.pdf'):
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        return ''