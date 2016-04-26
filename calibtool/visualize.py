import logging

logger = logging.getLogger(__name__)


def combine_by_site(site, analyzers, results):
    site_analyzers = [site + '_' + a for a in analyzers]
    logger.debug('site_analyzers: %s', site_analyzers)
    site_total = site + '_total'
    results[site_total] = results[site_analyzers].sum(axis=1)
    logger.debug('results[%s]=%s', site_total, results[site_total])