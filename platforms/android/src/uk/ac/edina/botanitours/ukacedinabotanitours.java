/*
       Licensed to the Apache Software Foundation (ASF) under one
       or more contributor license agreements.  See the NOTICE file
       distributed with this work for additional information
       regarding copyright ownership.  The ASF licenses this file
       to you under the Apache License, Version 2.0 (the
       "License"); you may not use this file except in compliance
       with the License.  You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

       Unless required by applicable law or agreed to in writing,
       software distributed under the License is distributed on an
       "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
       KIND, either express or implied.  See the License for the
       specific language governing permissions and limitations
       under the License.
 */

package uk.ac.edina.botanitours;

import android.os.Bundle;
import android.util.Log;
import org.apache.cordova.Config;
import org.apache.cordova.CordovaActivity;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

public class ukacedinabotanitours extends CordovaActivity
{
    @Override
    public void onCreate(Bundle savedInstanceState)
    {
        super.onCreate(savedInstanceState);
        super.init();
        super.loadUrl(Config.getStartUrl());

        try{
            File dbFile = getDatabasePath("botanitours.db");
            if(!dbFile.exists()){
                Log.v("sqlite", "Database doesn't exist. Copy it to : " + dbFile);
                this.copy(dbFile);
            }
            else{
                Log.v("sqlite", "Database exists: " + dbFile);
            }
        }
        catch (Exception e){
            e.printStackTrace();
        }
    }

    // copy db from assets to database location
    private void copy(File dbFile) throws IOException{
        String parentPath = dbFile.getParent();

        File filedir = new File(parentPath);
        if (!filedir.exists()) {
            if (!filedir.mkdirs()) {
                return;
            }
        }

        InputStream in = this.getApplicationContext().getAssets().open("db/botanitours.sqlite");
        //File newfile = new File(folder);
        OutputStream out = new FileOutputStream(dbFile);

        byte[] buf = new byte[1024];
        int len; while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
        in.close(); out.close();
        Log.v("sqlite", "finished copying");
    }
}
