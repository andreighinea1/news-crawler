import { 
    NAV_ITEM_TYPE_TITLE, 
    NAV_ITEM_TYPE_ITEM
} from 'constants/navigation.constant'

const navigationConfig = [
    {
		key: 'searchMenu',
		path: '',
		title: 'Search Menu',
		translateKey: 'nav.searchMenu.menu',
		icon: '',
		type: NAV_ITEM_TYPE_TITLE,
		authority: [],
		subMenu: [
            {
                key: 'searchMenu.searchNewsByTitle',
                path: '/search-menu-news-by-title',
                title: 'Search News By Title',
                translateKey: 'nav.searchMenu.searchNewsByTitle',
                icon: 'searchNewsByTitle',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: []
            },
            {
                key: 'searchMenu.newsQueryHistory',
                path: '/search-menu-news-query-history',
                title: 'News Query History',
                translateKey: 'nav.searchMenu.newsQueryHistory',
                icon: 'newsQueryHistory',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: []
            }
        ]
    }
]

export default navigationConfig