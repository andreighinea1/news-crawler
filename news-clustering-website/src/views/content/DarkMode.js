import React from 'react'
import ModeSwitcher from "../../components/template/ThemeConfigurator/ModeSwitcher";
import {HiOutlineCog} from "react-icons/hi";

const DarkMode = () => {
    return (
        <div className="flex flex-col w-auto justify-between">
            <div className="flex flex-col mr-2">
                <div className="flex items-center space-x-1.5 justify-between">
                    <div className="flex space-x-1 mt-auto">
                        <div className="text-2xl">
                            <HiOutlineCog/>
                        </div>
                        <h6>Dark Mode</h6>
                    </div>
                    <ModeSwitcher/>
                </div>
            </div>
        </div>
    )
}

export default DarkMode
