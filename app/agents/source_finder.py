from app.domain.schemas import Source


class SourceFinder:
    def find_seed_sources(self, idea: str) -> list[Source]:
        return [
            Source(
                title="Documentacao oficial do dominio",
                url=None,
                source_type="documentation",
                reliability_score=90,
                notes="Fonte prioritaria para APIs, limites, termos e comportamento oficial.",
            ),
            Source(
                title="Repositorios GitHub relacionados",
                url=None,
                source_type="github",
                reliability_score=70,
                notes="Bom para entender implementacoes existentes, manutencao e gaps.",
            ),
            Source(
                title="Foruns e comunidades do dominio",
                url=None,
                source_type="community",
                reliability_score=55,
                notes="Bom para dores reais, mas sujeito a vies e relatos anedoticos.",
            ),
            Source(
                title="Ferramentas concorrentes e alternativas",
                url=None,
                source_type="competitor",
                reliability_score=75,
                notes="Necessario para avaliar diferenciacao e escopo de MVP.",
            ),
        ]

