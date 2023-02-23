import React from 'react'
import authRoute from './authRoute'

export const publicRoutes = [
    ...authRoute
]

export const protectedRoutes = [
    {
        key: 'searchSimilarNews',
        path: '/search-menu-similar-news',
        component: React.lazy(() => import('views/content/SearchSimilarNews')),
        authority: [],
    },
    {
        key: 'queryHistory',
        path: '/search-menu-query-history',
        component: React.lazy(() => import('views/content/QueryHistory')),
        authority: [],
    },
    {
        key: 'queryResult',
        path: '/query-result',
        component: React.lazy(() => import('views/content/QueryResult')),
        authority: [],
    },
]