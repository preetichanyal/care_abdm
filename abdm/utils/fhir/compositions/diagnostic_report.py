from datetime import UTC, datetime

from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.composition import Composition, CompositionSection
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.meta import Meta
import json
import logging


logger = logging.getLogger(__name__)

from abdm.service.helper import uuid
from abdm.settings import plugin_settings as settings
from care.emr.models.diagnostic_report import DiagnosticReport as DiagnosticReportModel

CARE_IDENTIFIER_SYSTEM = settings.BACKEND_DOMAIN


class DiagnosticReportCompositionMixin:
    def _diagnostic_report_composition(
        self, diagnostic_report: DiagnosticReportModel, care_context_id: str
    ):
        encounter = diagnostic_report.encounter
        service_request = diagnostic_report.service_request

        organization = self._organization(encounter.facility)
        author_user = diagnostic_report.created_by

        author = (
          self._reference(self._practitioner(author_user))
          if author_user
          else self._reference(organization)
        )

        return Composition(
            id=care_context_id,
            meta=Meta(
                versionId="1",
                lastUpdated=datetime.now(UTC).isoformat(),
                profile=[
                    "https://nrces.in/ndhm/fhir/r4/StructureDefinition/DiagnosticReportRecord"
                ],
            ),
            identifier=Identifier(value=care_context_id),
            status="final",
            type=CodeableConcept(
                coding=[
                    Coding(
                        system="http://snomed.info/sct",
                        code="721981007",
                        display="Diagnostic studies report",
                    )
                ],
                text="Diagnostic Report",
            ),
            title="Diagnostic Report",
            date=datetime.now(UTC).isoformat(),
            section=[
                CompositionSection(
                    title=service_request.title,
                    code=self._coding_to_codable_concept(service_request.code),
                    entry=[self._reference(self._diagnostic_report(diagnostic_report))],
                ),
            ],
            subject=self._reference(self._patient(encounter.patient)),
            encounter=self._reference(self._encounter(encounter)),
            #author=[self._reference(self._organization(encounter.facility))],
            author=[author],
        )

    def create_diagnostic_report_record(
        self,
        diagnostic_report: DiagnosticReportModel,
        care_context_id: str = uuid(),
    ):
        return self._bundle(
            entries=[
                self._bundle_entry(
                    self._diagnostic_report_composition(
                        diagnostic_report, care_context_id
                    )
                ),
                *[self._bundle_entry(profile) for profile in self.cached_profiles()],
            ],
            care_context_id=care_context_id,
        )
