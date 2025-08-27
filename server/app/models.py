from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, BigInteger,
    ForeignKey, UniqueConstraint, CheckConstraint, Index, CHAR, Float
)
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


# -------------------
# Existing ClaimModel
# -------------------
class ClaimModel(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_text = Column(Text, nullable=False, unique=True)
    verdict = Column(String(255))
    source_url = Column(String(2048), nullable=False, unique=True)
    published_date = Column(Date)
    version = Column(Integer, default=1)
    short_points = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    simhash = Column(String(20), index=True)

    # Relations
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    fact_checker_id = Column(Integer, ForeignKey("actors.id", ondelete="SET NULL"))
    language = Column(Text)
    updated_at = Column(TIMESTAMP(timezone=True))

    source = relationship("Source", back_populates="claims")
    fact_checker = relationship("Actor", back_populates="fact_checked_claims")
    entities = relationship("Entity", secondary="claim_entities", back_populates="claims")
    events = relationship("ClaimEvent", back_populates="claim", cascade="all, delete-orphan")


# -------------------
# Sources
# -------------------
class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    domain = Column(CITEXT, nullable=False)
    kind = Column(Text, nullable=False)
    name = Column(Text)
    country_code = Column(CHAR(2))
    created_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)

    __table_args__ = (
        UniqueConstraint("domain", "kind"),
        CheckConstraint("kind IN ('fact_checker','news','social','gov','ngo','blog','forum','other')"),
        Index("idx_sources_domain", "domain"),
    )

    claims = relationship("ClaimModel", back_populates="source")
    actors = relationship("Actor", back_populates="source")
    events = relationship("ClaimEvent", back_populates="source")


# -------------------
# Actors
# -------------------
class Actor(Base):
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True)
    platform = Column(Text, nullable=False)
    handle = Column(CITEXT)
    display_name = Column(Text)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "handle"),
        CheckConstraint("platform IN ('x','reddit','telegram','youtube','facebook','instagram','news','website','fact_checker','other')"),
        Index("idx_actors_source_id", "source_id"),
    )

    source = relationship("Source", back_populates="actors")
    fact_checked_claims = relationship("ClaimModel", back_populates="fact_checker")
    events = relationship("ClaimEvent", back_populates="actor")
    metrics = relationship("ActorMetricsDaily", back_populates="actor")


# -------------------
# Entities & ClaimEntities
# -------------------
class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    name = Column(CITEXT, nullable=False)
    kind = Column(Text)
    lang = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "kind", "lang", name="uq_entity_name_kind_lang"),
        CheckConstraint("kind IN ('person','org','place','topic','other')"),
    )

    claims = relationship("ClaimModel", secondary="claim_entities", back_populates="entities")


class ClaimEntity(Base):
    __tablename__ = "claim_entities"

    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index("idx_claim_entities_claim", "claim_id"),
        Index("idx_claim_entities_entity", "entity_id"),
    )


# -------------------
# Claim Events
# -------------------
class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id = Column(BigInteger, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"))
    actor_id = Column(Integer, ForeignKey("actors.id", ondelete="SET NULL"))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"))
    event_type = Column(Text, nullable=False)
    url = Column(Text)
    content_excerpt = Column(Text)
    language = Column(Text)
    published_at = Column(TIMESTAMP(timezone=True), nullable=False)
    collected_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)
    reshares = Column(Integer, server_default="0", nullable=False)
    replies = Column(Integer, server_default="0", nullable=False)
    reactions = Column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        CheckConstraint("event_type IN ('said','shared','debunked','referenced')"),
        Index("idx_claim_events_claim_time", "claim_id", "published_at"),
        Index("idx_claim_events_actor_time", "actor_id", "published_at"),
        Index("idx_claim_events_source_time", "source_id", "published_at"),
        Index("idx_claim_events_type_time", "event_type", "published_at"),
    )

    claim = relationship("ClaimModel", back_populates="events")
    actor = relationship("Actor", back_populates="events")
    source = relationship("Source", back_populates="events")


# -------------------
# Metrics
# -------------------
class ActorMetricsDaily(Base):
    __tablename__ = "actor_metrics_daily"

    actor_id = Column(Integer, ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, primary_key=True)
    posts = Column(Integer, default=0, nullable=False)
    unique_claims = Column(Integer, default=0, nullable=False)
    origin_score = Column(Float)
    amplifier_score = Column(Float)
    coordinated_score = Column(Float)
    false_share_count = Column(Integer, default=0, nullable=False)
    trust_score = Column(Float)

    __table_args__ = (Index("idx_actor_metrics_trust", "date", "trust_score"),)

    actor = relationship("Actor", back_populates="metrics")


class SourceMetricsDaily(Base):
    __tablename__ = "source_metrics_daily"

    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, primary_key=True)
    posts = Column(Integer, default=0, nullable=False)
    unique_actors = Column(Integer, default=0, nullable=False)
    false_rate = Column(Float)
    accuracy_rate = Column(Float)
    avg_burstiness = Column(Float)
    trust_score = Column(Float)

    __table_args__ = (Index("idx_source_metrics_trust", "date", "trust_score"),)


# -------------------
# Variants
# -------------------
class VariantCluster(Base):
    __tablename__ = "variant_clusters"

    id = Column(BigInteger, primary_key=True)
    label = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)

    events = relationship("EventVariant", back_populates="variant")
    claims = relationship("ClaimVariant", back_populates="variant")


class EventVariant(Base):
    __tablename__ = "event_variants"

    event_id = Column(BigInteger, ForeignKey("claim_events.id", ondelete="CASCADE"), primary_key=True)
    variant_id = Column(BigInteger, ForeignKey("variant_clusters.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(TIMESTAMP(timezone=True), server_default="NOW()", nullable=False)

    __table_args__ = (Index("idx_event_variants_variant", "variant_id"),)

    variant = relationship("VariantCluster", back_populates="events")


class ClaimVariant(Base):
    __tablename__ = "claim_variants"

    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), primary_key=True)
    variant_id = Column(BigInteger, ForeignKey("variant_clusters.id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (Index("idx_claim_variants_variant", "variant_id"),)

    variant = relationship("VariantCluster", back_populates="claims")

# -------------------
# Variants
# -------------------
class ScraperRuns(Base):
    __tablename__ = "scraper_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_name = Column(String(255), nullable=False)
    last_run = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50))  # e.g. "success", "failed", "partial"
    total_fetched = Column(Integer, default=0, nullable=True)
    total_inserted = Column(Integer, default=0, nullable=True)