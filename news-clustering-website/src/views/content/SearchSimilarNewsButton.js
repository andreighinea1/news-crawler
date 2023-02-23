import React, { useState } from 'react'
import {Button} from 'components/ui'
import { HiOutlineSearch } from 'react-icons/hi'

const SearchSimilarNewsButton = (props) => {

    const { size, shape, loading, onClick } = props

    return (
        <div className="flex-wrap inline-flex xl:flex items-center gap-2">
            <Button className="mr-2"
                    variant="solid"
                    onClick={onClick}
                    loading={loading}
                    icon={<HiOutlineSearch />}
                    size={size}
                    shape={shape}
            >
                <span>Search News</span>
            </Button>
        </div>
    )
}

export default SearchSimilarNewsButton