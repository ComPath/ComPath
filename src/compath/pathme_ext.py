import logging

logger = logging.getLogger(__name__)

__all__ = [
    'add_pathme',
]


def add_pathme(app, admin, db):
    """Add pathme views."""
    from pathme_viewer.web.views import pathme, PathwayView
    from pathme_viewer.models import Pathway
    from pathme_viewer.manager import Manager as PathmeManager
    app.register_blueprint(pathme)
    admin.add_view(PathwayView(Pathway, db.session))

    app.pathme_manager = PathmeManager(engine=db.engine, session=db.session)
    logger.info('PathMe plugin has been imported')
